using System;
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;
using TMPro;
using System.Linq;
using Assets.Scripts.Components;

namespace Aituber
{
    public class TextToSpeech : MonoBehaviour
    {
        private const string apiUrl = Constants.SERVER_BASE_URL + "/voice/"; // APIのURLを指定します
        public TextMeshProUGUI responseText;
        public AudioSource annoAudioSource;
        public AudioSource narratorAudioSource;
        public bool isSpeaking = false; // 再生中かどうかのフラグ
        public int maxTextLength = 40; // 最大テキスト長

        public Queue<Conversation> conversations = new Queue<Conversation>();

        public Speech currentSpeech = null;

        public TalkSegment currentTalkSegment = null;

        private Queue<Speech> preparedSpeeches = new Queue<Speech>();
        public int speechGenerateTimeoutInSeconds = 120;
        public int maxAttemptCountOnSpeechAPI = 5;
        private int processingCount = 0;

        public QueueIndicator queueIndicator;

        public float narratorVolumeScale = 0.2f;

        public int QueuedConversations
        {
            get { return conversations.Count + preparedSpeeches.Count + processingCount; }
        }


        public void EnqueueConversation(Conversation conversation)
        {
            this.conversations.Enqueue(conversation);
        }

        public bool HasCapacityToEnqueue()
        {
            return this.preparedSpeeches.Count < 20;
        }

        public void Start()
        {
            monitorConversationQueue();
        }

        public bool HasNext()
        {
            return this.preparedSpeeches.Count > 0;
        }

        public async UniTask PlayNext()
        {
            if (this.isSpeaking) return;
            Speech nextSpeech = null;
            if (this.hasSpeechToUser(preparedSpeeches)) // ユーザからの準備済みの返答がすでにある時
            {
                while (this.preparedSpeeches.Count > 0)
                {
                    var nextSpeechCand = this.preparedSpeeches.Dequeue();
                    queueIndicator.RemoveFromIndicator(nextSpeechCand.Conversation.question);
                    if (!nextSpeechCand.Conversation.question.isAutoQuestion) // 自動生成ではない質問
                    {
                        nextSpeech = nextSpeechCand;
                        break;
                    }
                    else
                    {
                        Debug.Log("Skipping auto question:" + nextSpeechCand.Conversation.question.question);
                    }
                }
            }
            else
            {
                nextSpeech = this.preparedSpeeches.Dequeue();
                queueIndicator.RemoveFromIndicator(nextSpeech.Conversation.question);
            }
            this.isSpeaking = true;
            this.currentSpeech = nextSpeech;
            await SpeechTalkSegmentsInSeries(nextSpeech.talkSegments, 0.5);
            await UniTask.Delay(TimeSpan.FromSeconds(2));
            this.currentSpeech = null;
            this.isSpeaking = false;
        }

        public async UniTask monitorConversationQueue()
        {
            while (true)
            {
                if (this.conversations.Count > 0)
                {
                    Conversation nextConversation = null;
                    if (hasConversationsWithUser(this.conversations))
                    {
                        while(this.conversations.Count > 0)
                        {
                            var nextConversationCand = this.conversations.Dequeue();
                            if (!nextConversationCand.question.isAutoQuestion)
                            {
                                nextConversation = nextConversationCand;
                                break;
                            }
                            else
                            {
                                Debug.Log("Skipping auto question:" + nextConversationCand.question.question);
                                queueIndicator.RemoveFromIndicator(nextConversationCand.question);
                            }
                        }
                    }
                    else
                    {
                        nextConversation = this.conversations.Dequeue();
                    }
                    processingCount++;
                    await this.ProcessConversation(nextConversation);
                    processingCount--;
                }

                await UniTask.Delay(TimeSpan.FromSeconds(1));
            }
        }

        private async UniTask ProcessConversation(Conversation conv)
        {
            List<string> textSegments = SplitText(conv.response, maxTextLength);
            TalkSegment[] segments = new TalkSegment[textSegments.Count + 1];
            segments[0] = new TalkSegment(this.narratorAudioSource,conv.question.question,this.narratorVolumeScale,"slide_1",false,"考え中...");
            downloadSpeechesParallel(0, "azure", segments);
            for (int i = 1; i < textSegments.Count + 1; i++)
            {
                segments[i] = new TalkSegment(this.annoAudioSource,textSegments[i-1],1f,conv.imageFileName,true);
                downloadSpeechesParallel(i,"male", segments);
            }

            bool ready = false;
            for (int i = 0; i < speechGenerateTimeoutInSeconds; i++)
            {
                if (segments.All(s => s.IsAudioLoaded()))
                {
                    ready = true;
                    break;
                }

                await UniTask.Delay(TimeSpan.FromSeconds(1));
            }

            if (ready)
            {
                this.preparedSpeeches.Enqueue(new Speech(conv, segments));
            }
            else
            {
                Debug.LogWarning("Failed to generate speech audit within deadline");
                queueIndicator.RemoveFromIndicator(conv.question);
            }
        }

        List<string> SplitText(string text, int maxLength)
        {
            List<string> segments = new List<string>();
            string[] sentences = text.Split(new char[] {'。','\n'});

            string currentSegment = "";
            foreach (string sentence in sentences)
            {
                if (currentSegment.Length + sentence.Length <= maxLength)
                {
                    if (currentSegment.Length > 0)
                    {
                        currentSegment += "。";
                    }

                    currentSegment += sentence;
                }
                else
                {
                    if (currentSegment.Length > 0)
                    {
                        segments.Add(currentSegment + (sentence.Length > 0 ? "。" : ""));
                    }

                    currentSegment = sentence;
                }
            }

            if (currentSegment.Length > 0)
            {
                segments.Add(currentSegment);
            }

            return segments;
        }

        public async void TalkFromText(string text)
        {
            List<string> textSegments = SplitText(text, maxTextLength);
            isSpeaking = true;
            TalkSegment[] segments = new TalkSegment[textSegments.Count];

            for (int i = 0; i < textSegments.Count; i++)
            {
                segments[i] = new TalkSegment(this.annoAudioSource,textSegments[i],1f,"slide_1",true);
                downloadSpeechesParallel(i, "male", segments);
            }

            bool ready = false;
            for (int i = 0; i < speechGenerateTimeoutInSeconds; i++)
            {
                if (segments.All(s => s.IsAudioLoaded()))
                {
                    ready = true;
                    break;
                }

                await UniTask.Delay(TimeSpan.FromSeconds(1));
            }

            if (ready)
            {
                await SpeechTalkSegmentsInSeries(segments, 0.5);
            }
            else
            {
                Debug.LogWarning("Failed to generate speech audit within deadline");
            }

            isSpeaking = false;
        }

        public async UniTask SpeechTalkSegmentsInSeries(TalkSegment[] segments, double timeGapBetweenSegments)
        {
            foreach (TalkSegment segment in segments)
            {
                this.currentTalkSegment = segment; 
                await this.PlayAudio(segment.audioSource,segment.audioClip, segment.labelString,segment.audioVolume);
                await UniTask.Delay(TimeSpan.FromSeconds(timeGapBetweenSegments));
            }
            this.currentTalkSegment = null;
        }

        public async UniTask PlayAudio(AudioSource source,AudioClip clip, string textToShow,float volume)
        {
            if (clip != null)
            {
                float prevVolume = source.volume;
                source.volume = prevVolume * volume;
                source.clip = clip;
                var trimmed = textToShow.Trim('\n', '\r', ' ', '\t');
                responseText.text = trimmed;
                source.Play();
                await UniTask.WaitUntil(() => !source.isPlaying);
                source.volume = prevVolume;
            }
        }

        async UniTask downloadSpeechesParallel(int index, string version, TalkSegment[] segments)
        {
            segments[index].audioClip = await DownloadAudio(segments[index].text,version);
        }


        public async UniTask<AudioClip> DownloadAudio(string text,string version)
        {
            if (string.IsNullOrEmpty(text)) return null;
            var currentWaitTime = 1;
            for (var attempt = 0; attempt < 10; attempt++)
            {
                try
                {
                    string textToShow = text;

                    string textToGenerateVoice = ReplaceTextForSpeech(text);

                    string url = apiUrl +version + "?text=" + UnityWebRequest.EscapeURL(textToGenerateVoice) + "&model_id=0";

                    UnityWebRequest www = UnityWebRequest.PostWwwForm(url, "");

                    await www.SendWebRequest();

                    if (www.result != UnityWebRequest.Result.Success)
                    {
                        Debug.LogError("Error: " + www.error);

                        await UniTask.Delay(TimeSpan.FromSeconds(currentWaitTime));
                        currentWaitTime *= 2;
                        continue;
                    }

                    // APIのValidation Error時の詳細な内容をログに表示
                    if (www.responseCode == 422)
                    {
                        string errorResponse = www.downloadHandler.text;
                        Debug.LogWarning(errorResponse);
                        await UniTask.Delay(TimeSpan.FromSeconds(currentWaitTime));
                        currentWaitTime *= 2;
                        continue;
                    }

                    string contentType = www.GetResponseHeader("Content-Type");

                    string responseData = www.downloadHandler.text;

                    byte[] audioData = www.downloadHandler.data;

                    AudioClip audioClip = WAVUtil.ToAudioClip(audioData);
                    return audioClip;
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"Error: {e.Message}");
                    await UniTask.Delay(TimeSpan.FromSeconds(currentWaitTime));
                    currentWaitTime *= 2;
                    continue;
                }
            }

            return null;
        }


        // テキストを変換するメソッド
        string ReplaceTextForSpeech(string text)
        {
            return text.Replace("安野", "庵野").Replace("元々", "もともと");
        }

        bool hasSpeechToUser(Queue<Speech> preparedSpeeches)
        {
            var array = preparedSpeeches.ToArray();
            return array.Any(x => !x.Conversation.question.isAutoQuestion);
        }

        bool hasConversationsWithUser(Queue<Conversation> conversation)
        {
            var array = conversation.ToArray();
            return array.Any(x => !x.question.isAutoQuestion);
        }
    }

    public static class WAVUtil
    {
        public static AudioClip ToAudioClip(byte[] wavBytes)
        {
            // WAVヘッダーを解析してオーディオデータを抽出
            int headerSize = 44;
            int dataSize = BytesToInt(wavBytes, 40);
            float[] audioData = new float[dataSize / 2];

            for (int i = 0; i < audioData.Length; i++)
            {
                audioData[i] = (short) (BytesToInt16(wavBytes, headerSize + 2 * i)) / 32768.0f;
            }

            // AudioClipを作成
            AudioClip audioClip = AudioClip.Create("AudioClip", audioData.Length, 1, 44100, false);
            audioClip.SetData(audioData, 0);

            return audioClip;
        }

        private static int BytesToInt(byte[] bytes, int offset)
        {
            return (bytes[offset + 3] << 24) |
                   (bytes[offset + 2] << 16) |
                   (bytes[offset + 1] << 8) |
                   bytes[offset];
        }

        private static short BytesToInt16(byte[] bytes, int offset)
        {
            return (short) ((bytes[offset + 1] << 8) | bytes[offset]);
        }
    }

    /// <summary>
    /// 安野さんがしゃべるクリップとその字幕のセット
    /// </summary>
    public class TalkSegment
    {
        public AudioSource audioSource;

        public AudioClip audioClip = null;

        public readonly string text;

        public float audioVolume;

        public readonly string labelString;

        public string slidePath;

        public bool isAnno;

        public TalkSegment(AudioSource audioSource,string text,float audioVolume,string slidePath,bool isAnno,string labelString = "")
        {
            this.audioSource = audioSource;
            if(labelString == "")
            {
                labelString = text;
            }
            this.labelString = labelString;
            this.text = text;
            this.audioVolume = audioVolume;
            this.slidePath = slidePath; 
            this.isAnno = isAnno;
        }

        public bool IsAudioLoaded()
        {
            return audioClip != null || string.IsNullOrEmpty(this.text);
        }
    }

    public class Speech
    {
        public Conversation Conversation = null;

        public TalkSegment[] talkSegments = null;

        public Speech(Conversation conversation, TalkSegment[] talkSegments)
        {
            this.Conversation = conversation;
            this.talkSegments = talkSegments;
        }
    }
}