using System.Collections.Generic;
using Aituber;
using UnityEditor.PackageManager.Requests;
using UnityEngine;

namespace Aituber
{
    public enum MotionType
    {
        Idle = 1,
        HandShake = 6,
        Waving = 7,
        Request = 6,
    }


    public class RandomAnimation1 : MonoBehaviour
    {
        public Animator animator; // Animatorコンポーネントへの参照
        public int numberOfStates = 7; // ステートの総数
        public TextToSpeech textToSpeech; // TextToSpeechコンポーネントへの参照
        public QueueManager queueManager;
        public CameraSwitcher cameraSwitcher;


        List<string> handshake = new List<string> { "握手" };
        List<string> waving = new List<string> { "安野たかひろ", "安野", "たかひろ", "こんにちは", "おはよう", "こんばんは" };
        List<string> request_q = new List<string> { "ほしい", "欲しい" };


        private bool wasSpeaking = false; // 前回の isSpeaking 状態を記録
        private static readonly int RandomState = Animator.StringToHash("RandomState");

        private Speech prevSpeech = null;

        void Start()
        {
            SetDefaultState();
        }

        public void SetAnimation(MotionType mType)
        {
            animator.SetInteger(RandomState, (int)mType);
        }

        void Update()
        {
            if (textToSpeech != null)
            {
                if (textToSpeech.currentSpeech != prevSpeech)
                {
                    prevSpeech = textToSpeech.currentSpeech;
                    OnChangeSpeech();
                }
            }
        }

        void OnChangeSpeech()
        {
            if (textToSpeech.currentTalkSegment != null && textToSpeech.currentTalkSegment.isAnno)
            {
                var question = queueManager.textToSpeech.currentSpeech?.Conversation?.question?.question ?? "";
                var answer = queueManager.textToSpeech.currentSpeech?.Conversation?.response ?? "";
                if (ContainsAny(question, handshake) || ContainsAny(answer, handshake))
                {
                    animator.SetInteger(RandomState, 6);
                    cameraSwitcher.ChangeCameraTo2();
                }
                else if (ContainsAny(question, waving))
                {
                    animator.SetInteger(RandomState, 7);
                    cameraSwitcher.ChangeCameraTo1();
                }
                else if (ContainsAny(question, request_q))
                {
                    animator.SetInteger(RandomState, 3);
                    cameraSwitcher.ChangeCameraTo1();
                }
                else
                {
                    ChangeAnimationStateWhileSpeaking();
                    cameraSwitcher.ChangeCameraTo1();

                }

                wasSpeaking = true;
            }
            else
            {
                SetDefaultState();
                cameraSwitcher.ChangeCameraTo1();
                wasSpeaking = false;
            }
        }

        bool ContainsAny(string text, List<string> words)
        {
            foreach (string word in words)
            {
                if (text.Contains(word))
                {
                    return true;
                }
            }

            return false;
        }

        void ChangeAnimationState()
        {
            int randomState = Random.Range(1, numberOfStates + 1); // ランダムな数値生成
            animator.SetInteger(RandomState, randomState); // Animatorのパラメータを設定
        }

        void ChangeAnimationStateWhileSpeaking()
        {
            List<int> states = new List<int> { 2, 3 };
            int randomState = states[Random.Range(0, states.Count)]; // リストからランダムに選択
            animator.SetInteger(RandomState, randomState); // Animatorのパラメータを設定
        }

        void SetDefaultState()
        {
            animator.SetInteger(RandomState, 1); // デフォルトステートに設定
        }

        void HandleSpeechComplete()
        {
            SetDefaultState(); // 音声再生が完了したらデフォルトステートに戻す
        }
    }
}