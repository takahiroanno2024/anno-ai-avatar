using System.Collections;
using System.Collections.Generic;
using Aituber;
using UnityEditor;
using UnityEngine;

public class QueueIndicator : MonoBehaviour
{
    public GameObject indicatorParent;

    public GameObject indicatorPrefab;

    [SerializeField]
    private TMPro.TextMeshProUGUI counterLabel;

    [HideInInspector]
    private List<Question> questionList = new List<Question>();

    private Dictionary<GUID, QueueIconItem> queueItems = new Dictionary<GUID, QueueIconItem>();

    private bool invalidate = false;

    public int QueueLength {  get { return queueItems.Count; } }

    public void AppendInIndicator(Question question)
    {
        questionList.Add(question);
        invalidate = true;
    }

    public void RemoveFromIndicator(Question question)
    {
        questionList.Remove(question);
        invalidate = true;
    }

    // Update is called once per frame
    void Update()
    {
        if (invalidate)
        {
            var used = new HashSet<GUID>();
            for (var questionIndex = 0; questionIndex < questionList.Count; questionIndex++)
            {
                var question = questionList[questionIndex];
                if (!queueItems.ContainsKey(question.id))
                {
                    var item = GameObject.Instantiate(indicatorPrefab, indicatorParent.transform);
                    var generatedIconItem = item.GetComponent<QueueIconItem>();
                    generatedIconItem.GetComponent<RectTransform>().anchoredPosition = new Vector2(500, 0);
                    generatedIconItem.ShowUp(question.imageIcon);
                    queueItems.Add(question.id, generatedIconItem);
                }
                used.Add(question.id);
                var iconItem = queueItems[question.id];
                iconItem.AdjustAnchorLocation(new Vector2(0, 0) + new Vector2(43 * questionIndex, 0));
            }
            var remove = new HashSet<GUID>();
            foreach (var question in queueItems)
            {
                if (!used.Contains(question.Key))
                {
                    remove.Add(question.Key);
                }
            }
            foreach (var item in remove)
            {
                var removeGameObject = queueItems[item];
                removeGameObject.Dismiss();
                queueItems.Remove(item);
            }
            this.counterLabel.text = string.Format("{0}åè",queueItems.Count);
            invalidate = false;

        }
    }
}
