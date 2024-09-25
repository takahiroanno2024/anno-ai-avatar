using UnityEngine;
using UnityEngine.UI;

namespace Aituber
{
    public class SlideDisplayer : MonoBehaviour
    {
        public TextToSpeech textToSpeech;
        public QueueManager queueManager; // QueueManagerの参照
        public Image displayImage; // 表示するImageコンポーネント
        public Sprite defaultSprite; // 画像が無い場合に表示するデフォルトのスプライト

        private bool wasSpeaking = false;
        private string prevImage = "";

        void Start()
        {
            if (queueManager == null)
            {
                Debug.LogError("QueueManagerが設定されていません。");
                return;
            }

            UpdateImage("slide_1");
        }

        void Update()
        {
            if (textToSpeech != null)
            {
                var currentSlide = textToSpeech.currentTalkSegment?.slidePath ?? "slide_1";
                if (currentSlide != prevImage)
                {
                    prevImage = currentSlide;
                    UpdateImage(currentSlide);
                }
            }
        }

        public void UpdateImage(string fileName)
        {
            string replacedFilename = fileName.Replace(".png", "");
            string imageFilename = "Slides/manifest_demo_PDF/" + replacedFilename;
            Debug.Log("表示スライド - " + imageFilename);

            if (!string.IsNullOrEmpty(imageFilename))
            {
                // Resourcesフォルダから画像を読み込む
                Sprite newSprite = Resources.Load<Sprite>(imageFilename);
                if (newSprite != null)
                {
                    displayImage.sprite = newSprite;
                    displayImage.enabled = true;
                }
                else
                {
                    Debug.LogError($"画像ファイルが見つかりません: {imageFilename}");
                    SetDefaultSlide();
                }
            }
            else
            {
                SetDefaultSlide();
            }
        }

        public void SetDefaultSlide()
        {
            displayImage.sprite = defaultSprite;
            displayImage.enabled = (defaultSprite != null);
            if (defaultSprite == null)
            {
                Debug.LogWarning("デフォルトのスプライトが設定されていません。");
            }
        }

        public void HideSlide()
        {
            displayImage.enabled = false;
        }
    }
}