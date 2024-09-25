using TMPro;
using UnityEngine;

namespace Aituber
{
    public class InputManager : MonoBehaviour
    {
        public TMP_InputField inputField;
        public QueueManager queueManager;

        void Start()
        {
            inputField.onEndEdit.AddListener(HandleEndEdit);
        }

        private void HandleEndEdit(string text)
        {
            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
            {
                queueManager.AddTextToQueue(new Question(text,"–¼–³‚µ‚³‚ñ","",true));
            }
        }
    }
}