using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using TMPro;
using UnityEngine.Serialization;

namespace Aituber
{
    public class CommentPanelManager : MonoBehaviour
    {
        [SerializeField] private GameObject commentPanelParent;
        [SerializeField] private GameObject commentPanelPrefab;
        private CommentPanelItem currentCommentPanel;
        public QueueManager queueManager;

        public void ShowUserComment(string question, string userName, string userIcon)
        {
            if (question == "")
            {
                if (this.currentCommentPanel != null)
                {
                    this.currentCommentPanel.Dismiss();
                }
                this.currentCommentPanel = null;
                return;
            }
            var currentCommentPanelGameObject = GameObject.Instantiate(commentPanelPrefab, commentPanelParent.transform);
            var currentCommentPanel = currentCommentPanelGameObject.GetComponent<CommentPanelItem>();
            if (this.currentCommentPanel != null)
            {
                this.currentCommentPanel.Dismiss();
            }
            this.currentCommentPanel = currentCommentPanel;
            currentCommentPanel.ShowUp(question, userName, userIcon);
        }


        public string CreateFallbackJson()
        {
            // ランダムにメッセージを選択するためのリスト
            List<string> messages = new List<string>
            {
                // "握手してください！",
                // "あなたの名前は？",
                // "初見です",
                "教育をどうしていきたい？",
                // "どんな仕事してるんですか？",
                "いまの民主主義についてどう思う？",
                "プロフィールを教えて",
                "どんな政策を考えてるの？",
                "少子高齢化対策はどうする？"
            };

            string username = "名無し";

            // System.Random クラスのインスタンスを作成（UnityEngine.Randomとの衝突を避ける）
            System.Random random = new System.Random();

            // リストからランダムにメッセージを選択
            string randomMessage = messages[random.Next(messages.Count)];

            // シミュレートされた最小限の有効なJSONレスポンスを作成
            string mockJson = "{"
                              + "\"nextPageToken\": \"\","
                              + "\"items\": ["
                              + "    {"
                              + "        \"snippet\": {"
                              + "            \"displayMessage\": \"" + randomMessage + "\","
                              + "            \"textMessageDetails\": {"
                              + "                \"messageText\": \"" + randomMessage + "\""
                              + "            }"
                              + "        },"
                              + "        \"authorDetails\": {"
                              + "            \"displayName\": \"" + username + "\","
                              + "            \"profileImageUrl\": \"xxx\""
                              + "        }"
                              + "    }"
                              + "]"
                              + "}";
            return mockJson;
        }
    }
}