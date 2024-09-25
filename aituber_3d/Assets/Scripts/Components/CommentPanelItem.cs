using System.Collections;
using System.Collections.Generic;
using Aituber;
using DG.Tweening;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using System;

public class CommentPanelItem : MonoBehaviour
{
    [SerializeField] private Text userNameText;
    [SerializeField] private Image userIconImage;
    [SerializeField] private Text chatDisplayText;

    public void ShowUp(string comment,string authorName,string iconUrl)
    {
        chatDisplayText.text = comment;
        userNameText.text = (authorName ?? "名無し") + " さんのコメント";
        UpdateUserIcon(iconUrl);
        var rectTransform = GetComponent<RectTransform>();
        var targetPosition = rectTransform.anchoredPosition;
        rectTransform.anchoredPosition = new Vector2(-200, 0);
        rectTransform.DOAnchorPos(targetPosition, 1);
    }

    public async UniTask Dismiss()
    {
        RectTransform rectTransform = GetComponent<RectTransform>();
        rectTransform.DOAnchorPos(new Vector2(-800,0), 1);
        await UniTask.Delay(TimeSpan.FromSeconds(1));

        GameObject.Destroy(this.gameObject);
    }

    private async void UpdateUserIcon(string userIconUrl)
    {
        var defaultIcon = LoadDefaultIcon();
        userIconImage.sprite = defaultIcon;

        var loaded = await FetchImage(userIconUrl);
        if (loaded != null)
        {
            userIconImage.sprite = loaded;
        }
    }

    private async UniTask<Sprite> FetchImage(string url)
    {
        try
        {
            UnityWebRequest webRequest = UnityWebRequestTexture.GetTexture(url);
            await webRequest.SendWebRequest();

            if (webRequest.result != UnityWebRequest.Result.Success)
            {
                Debug.Log("Failed to load image: " + webRequest.error);
                return null;
            }

            Texture2D texture = DownloadHandlerTexture.GetContent(webRequest);
            var sprite = Sprite.Create(texture, new Rect(0, 0, texture.width, texture.height), Vector2.zero);
            return sprite;
        }
        catch
        {
            return null;
        }
    }

    private Sprite LoadDefaultIcon()
    {
        // 指定のSpriteをResourcesフォルダからロードする処理
        Sprite specifiedSprite = Resources.Load<Sprite>("Sprites/robot");
        return specifiedSprite;
    }
}
