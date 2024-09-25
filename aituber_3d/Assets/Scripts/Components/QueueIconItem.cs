using System.Collections;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using DG.Tweening;
using DG.Tweening.Core;
using DG.Tweening.Plugins.Options;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class QueueIconItem : MonoBehaviour
{
    public Image iconImage;
    private TweenerCore<Vector2, Vector2, VectorOptions> currentTween;

    public void ShowUp(string imageUrl)
    {
        UpdateImage(imageUrl);
    }

    public void AdjustAnchorLocation(Vector2 loc)
    {
        var rectTransform = this.GetComponent<RectTransform>();
        if (this.currentTween != null) {
            this.currentTween.Kill(false);
        }
        this.currentTween = rectTransform.DOAnchorPos(loc,0.5f);
    }

    public void Dismiss()
    {
        GameObject.Destroy(gameObject);
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
