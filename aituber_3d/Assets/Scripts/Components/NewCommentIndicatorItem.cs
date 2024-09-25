using System.Collections;
using System.Collections.Generic;
using Aituber;
using Cysharp.Threading.Tasks;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class NewCommentIndicatorItem : MonoBehaviour
{

    public Image iconImage;

    public Text question;

    public Text userName;

    public void SetQuestion(Question q)
    {
        this.question.text = q.question;
        this.userName.text = q.userName;
        UpdateImage(q.imageIcon);
    }

    public async UniTask UpdateImage(string url)
    {
        var defaultIcon = LoadDefaultIcon();
        iconImage.sprite = defaultIcon;

        if (url.StartsWith("http"))
        {
            var loaded = await FetchImage(url);
            if (loaded != null)
            {
                iconImage.sprite = loaded;
            }
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
