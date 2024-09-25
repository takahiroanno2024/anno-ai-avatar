using System;
using System.Collections;
using System.Collections.Generic;
using Aituber;
using Cysharp.Threading.Tasks;
using UnityEngine;
using DG.Tweening;

public class NewCommentIndicatorQueue : MonoBehaviour
{
    public GameObject prefabSource;

    public GameObject parentObject;

    public Queue<Question> questions = new Queue<Question>();

    public float lifeTimeInSeconds = 3;

    private void Start()
    {
        ProcessNewCommentQueue();
    }

    async UniTask ProcessNewCommentQueue()
    {
        while (true)
        {
            if (questions.Count == 0)
            {
                await UniTask.Delay(TimeSpan.FromSeconds(1));
            }
            else
            {
                var easeOutTime = 0.2f;
                var question = questions.Dequeue();
                var go = GameObject.Instantiate(prefabSource, parentObject.transform);
                go.GetComponent<NewCommentIndicatorItem>().SetQuestion(question);
                var rt = go.GetComponent<RectTransform>();
                rt.anchoredPosition = new Vector2(400, 0);
                rt.DOAnchorPos(new Vector2(0, 0), 0.8f).SetEase(Ease.OutCubic);
                await UniTask.Delay(TimeSpan.FromSeconds(lifeTimeInSeconds-easeOutTime));
                rt.DOAnchorPos(new Vector2(400, 0), easeOutTime).SetEase(Ease.InCubic);
                await UniTask.Delay(TimeSpan.FromSeconds(easeOutTime));
                GameObject.Destroy(go);
            }
        }
    }
}
