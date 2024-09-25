using UnityEngine;
using TMPro;

namespace Aituber
{
    public class SubtitleManager : MonoBehaviour
    {
        // public TextMeshProUGUI responseText;
        public TextToSpeech textToSpeech;
        public TMP_InputField answerInputField;

        private string text;

        public void ShowStartMessage()
        {
            text = "こんにちは！　私は東京都知事候補に立候補した安野たかひろのAIエージェントです。安野たかひろのマニフェストを学習し、みなさんの疑問にお答えしたり、要望をお聞きします！"; // 開始時のメッセージ
            // 長文テスト用メッセージ
            // text = "こんにちは、皆さん！ようこそ、私のチャンネルへ！初めての方も、いつも見てくれている方も、本当にありがとうございます。今日は皆さんと一緒に楽しい時間を過ごしたいと思っていますので、ぜひリラックスして楽しんでください。チャンネル登録がまだの方は、ぜひ登録してくれると嬉しいです。コメントや高評価も励みになりますので、よろしくお願いします！それでは、さっそく始めましょう。今日の配信、楽しんでいきましょう！最近、皆さんはどうお過ごしですか？私は最近、新しい趣味を見つけました。実は、ガーデニングを始めたんです。最初はちょっと手間がかかるかなと思っていたんですが、毎日少しずつ植物が成長していくのを見るのがとても楽しいんです。特に今は春なので、お花が次々に咲いていて、とてもきれいです。"; // 開始時のメッセージ
            textToSpeech.TalkFromText(text);
        }

        public void ShowEndMessage()
        {
            text = "これで本日の配信は終了です。お疲れ様でした！"; // 終了時のメッセージ
            textToSpeech.TalkFromText(text);
        }


        public void HandleInputFieldEnter(string userInput)
        {
            if (Input.GetKeyDown(KeyCode.Return))
            {
                textToSpeech.TalkFromText(userInput);
                answerInputField.text = ""; // Clear the input field after submitting
            }
        }

        void Start()
        {
            answerInputField.onEndEdit.AddListener(HandleInputFieldEnter);
        }
    }
}