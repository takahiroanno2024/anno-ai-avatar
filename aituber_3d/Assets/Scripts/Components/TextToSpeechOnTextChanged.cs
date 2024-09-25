using UnityEngine;
using TMPro;

namespace Aituber
{
    public class TextToSpeechOnTextChanged : MonoBehaviour
    {
        public TextMeshProUGUI responseText;
        public TextToSpeech textToSpeech;

        private string lastText;

        void Start()
        {
            // 初期のテキストを取得
            lastText = responseText.text;
        }

        void Update()
        {
            // テキストが変更されたかどうかを確認
            if (responseText.text != lastText)
            {
                // テキストが変更されたらtextToSpeechを実行
                textToSpeech.TalkFromText(responseText.text);
                // 変更後のテキストを記憶
                lastText = responseText.text;
            }
        }
    }
}