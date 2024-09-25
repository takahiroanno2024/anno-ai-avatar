using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Collections.Generic;
using System.Linq;
using Cysharp.Threading.Tasks;
using System;
using Assets.Scripts.Components;

namespace Aituber
{
    [System.Serializable]
    public class YouTubeChatResponse
    {
        public string nextPageToken;
        public Item[] items;

        [System.Serializable]
        public class Item
        {
            public Snippet snippet;
            public AuthorDetails authorDetails;
        }

        [System.Serializable]
        public class Snippet
        {
            public string displayMessage;
            public TextMessageDetails textMessageDetails;
        }

        [System.Serializable]
        public class TextMessageDetails
        {
            public string messageText;
        }

        [System.Serializable]
        public class AuthorDetails
        {
            public string displayName;
            public string profileImageUrl;
        }
    }

    [Serializable]
    public class YouTubeChatResponseV2
    {
        [Serializable]
        public class Message
        {
            public string video_id;

            public string message_id;

            public string message_text;

            public string author_name;

            public string author_image_url;
        }

        public Message[] messages;
    }

    public class YouTubeChatDisplay : MonoBehaviour
    {
        public Button fetchCommentsButton;
        public Button stopChatButton;

        private const string CHAT_API_URL = Constants.SERVER_BASE_URL + "/youtube/chat_message";
        private bool isRequesting = false; // リクエスト中かどうかのフラグ
        private bool stopRequested = false; // リクエストの停止を示すフラグ

        // private string stopWordsFilePath = "Text/stopwords";
        private string stopWordsDirectoryPath = "Text";
        private List<string> bannedPhrases = new List<string>();

        public CommentPanelManager commentPanelManager;

        void Start()
        {
            fetchCommentsButton.onClick.AddListener(OnFetchCommentsButtonClicked);
            stopChatButton.onClick.AddListener(StopFetchComment);

            // Resourcesフォルダ内のTextフォルダ直下のテキストファイルをすべて取得
            TextAsset[] textFiles = Resources.LoadAll<TextAsset>(stopWordsDirectoryPath);
            if (textFiles != null && textFiles.Length > 0)
            {
                foreach (var textFile in textFiles)
                {
                    var words = textFile.text.Split('\n')
                        .Select(word => word.Trim())
                        .Where(word => !string.IsNullOrEmpty(word))
                        .Where(word => !word.StartsWith("//")); // 行の先頭に"//"がある場合は無視（ストップされない）

                    bannedPhrases.AddRange(words);
                }
            }
            else
            {
                Debug.LogError("No stop words files found in Resources/Text/");
            }
            FetchCommentAsync();
        }

        async UniTask FetchCommentAsync()
        {
            while (true)
            {
                if (!stopRequested)
                {
                    var response = await GetChatData(CHAT_API_URL);
                    if (response != null) {
                        var count = 0;
                        foreach (var message in response.messages)
                        {
                            string messageText = message.message_text;

                            string messageTextFullKana = KanaConverter.ConvertHalfWidthToFullWidthKana(messageText);
                            string messageTextHanAlp = HankakuAlphabet.ConvertZenkakuToHankaku(messageTextFullKana);


                            if (!bannedPhrases.Any(word => messageTextHanAlp.Contains(word)))
                            {
                                count ++;
                                commentPanelManager.queueManager.AddTextToQueue(new Question(messageTextHanAlp, message.author_name, message.author_image_url,false));
                            }
                            else
                            {
                                Debug.LogWarning(string.Format("BANワード検知:{0}",messageTextHanAlp));
                            }
                        }
                        if (count > 0)
                        {
                            Debug.Log(string.Format("Enqueued {0} YT comments",count));
                        }
                    }
                    await UniTask.Delay(TimeSpan.FromSeconds(1));
                }
            }
        }

        void OnDestroy()
        {
            // オブジェクト破棄時にイベントリスナーを解除
            fetchCommentsButton.onClick.RemoveListener(OnFetchCommentsButtonClicked);
        }

        void OnFetchCommentsButtonClicked()
        {
            stopRequested = false; // チャット開始時に停止フラグをリセット
        }


        private void StopFetchComment()
        {
            stopRequested = true; // 停止フラグを設定
        }


        async UniTask<YouTubeChatResponseV2> GetChatData(string url)
        {
            try
            {
                using (UnityWebRequest webRequest = UnityWebRequest.Get(url))
                {
                    await webRequest.SendWebRequest();

                    if (webRequest.result != UnityWebRequest.Result.Success)
                    {
                        Debug.Log("Info: Error in getting YTcomment - " + webRequest.downloadHandler.text);
                        return null;
                    }
                    else
                    {
                        string receivedJson = webRequest.downloadHandler.text;
                        // Parse the JSON to check if the items array is empty
                        YouTubeChatResponseV2 response = JsonUtility.FromJson<YouTubeChatResponseV2>(receivedJson);


                        return response;
                    }
                }
            }
            catch (Exception e)
            {
                return null;
            }
        }
    }
}