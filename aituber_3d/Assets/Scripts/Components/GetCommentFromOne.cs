using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using WebSocketSharp;
using UnityEngine.Networking;
using Assets.Scripts.Components;
using UnityEditor;

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WebSocketSharp;
using UnityEngine.Networking;

using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using WebSocketSharp;
using UnityEngine.Networking;
using System.Collections.Concurrent;

public class UnityMainThreadDispatcher : MonoBehaviour
{
    private static UnityMainThreadDispatcher _instance;
    private static readonly Queue<Action> _executionQueue = new Queue<Action>();

    public static UnityMainThreadDispatcher Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindObjectOfType<UnityMainThreadDispatcher>();
                if (_instance == null)
                {
                    GameObject go = new GameObject("UnityMainThreadDispatcher");
                    _instance = go.AddComponent<UnityMainThreadDispatcher>();
                    DontDestroyOnLoad(go);
                }
            }
            return _instance;
        }
    }

    public void Update()
    {
        lock(_executionQueue)
        {
            while (_executionQueue.Count > 0)
            {
                _executionQueue.Dequeue().Invoke();
            }
        }
    }

    public void Enqueue(Action action)
    {
        lock (_executionQueue)
        {
            _executionQueue.Enqueue(action);
        }
    }
}

public class GetCommentFromOne : MonoBehaviour
{
    private WebSocket ws;
    private string serverUrl = Constants.SERVER_BASE_URL + "/youtube/chat_message";
    private string webSocketUrl = "ws://127.0.0.1:11180/sub";
    private float reconnectDelay = 5f;
    private bool isReconnecting = false;

    void Start()
    {
        // Ensure UnityMainThreadDispatcher is initialized
        UnityMainThreadDispatcher.Instance.Enqueue(() => {});
        ConnectWebSocket();
    }

    void ConnectWebSocket()
    {
        ws = new WebSocket(webSocketUrl);

        ws.OnMessage += (sender, e) =>
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() => HandleWebSocketMessage(e.Data));
        };

        ws.OnError += (sender, e) =>
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() => Debug.LogError($"WebSocket error: {e.Message}"));
        };

        ws.OnClose += (sender, e) =>
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() => 
            {
                Debug.Log($"WebSocket connection closed. Code: {e.Code}, Reason: {e.Reason}");
                if (!isReconnecting)
                {
                    StartCoroutine(ReconnectWithDelay());
                }
            });
        };

        ws.OnOpen += (sender, e) =>
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() => 
            {
                Debug.Log("WebSocket connection opened");
                isReconnecting = false;
            });
        };

        try
        {
            ws.ConnectAsync();
        }
        catch (Exception ex)
        {
            Debug.LogError($"Error connecting to WebSocket: {ex.Message}");
            StartCoroutine(ReconnectWithDelay());
        }
    }

    void HandleWebSocketMessage(string message)
    {
        try
        {
            var data = JsonUtility.FromJson<WebSocketData>(message);
            if (data != null && data.type == "comments")
            {
                Debug.Log($"WebSocket message received: {message}");
                StartCoroutine(ProcessComments(data.data.comments));
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error processing WebSocket message: {e.Message}");
        }
    }

    IEnumerator ProcessComments(List<CommentData> comments)
    {
        foreach (var comment in comments)
        {
            yield return StartCoroutine(PostCommentToServer(comment));
        }
    }

    IEnumerator PostCommentToServer(CommentData comment)
    {
        var commentToSend = new CommentToSend
        {
            live_id = comment.data.liveId,
            message_id = comment.data.id,
            name = comment.data.name,
            message = comment.data.comment,
            profile = comment.data.profileImage
        };
        string jsonBody = JsonUtility.ToJson(commentToSend);

        using (UnityWebRequest www = new UnityWebRequest(serverUrl, "POST"))
        {
            byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");
            www.SendWebRequest();
            yield return UnityWebRequest.Result.Success;
        }
    }

    IEnumerator ReconnectWithDelay()
    {
        isReconnecting = true;
        Debug.Log("Attempting to reconnect...");

        yield return new WaitForSeconds(reconnectDelay);

        ConnectWebSocket();
    }

    void OnDestroy()
    {
        if (ws != null && ws.ReadyState == WebSocketState.Open)
        {
            ws.Close();
        }
    }

    void Update()
    {
        if (ws == null || (!ws.IsAlive && !isReconnecting))
        {
            StartCoroutine(ReconnectWithDelay());
        }
    }
}



[Serializable]
public class WebSocketData
{
    public string type;
    public CommentDataContainer data;
}

[Serializable]
public class CommentDataContainer
{
    public List<CommentData> comments;
}

[Serializable]
public class CommentData
{
    public CommentDataContent data;
}

[Serializable]
public class CommentDataContent
{
    public string liveId;
    public string id;
    public string name;
    public string comment;
    public string profileImage;
}

[Serializable]
public class CommentToSend
{
    public string live_id;
    public string message_id;
    public string name;
    public string message;
    public string profile;
}