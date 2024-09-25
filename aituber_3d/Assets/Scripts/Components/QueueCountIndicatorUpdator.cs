using System.Collections;
using System.Collections.Generic;
using Aituber;
using TMPro;
using UnityEngine;

public class QueueCountIndicatorUpdator : MonoBehaviour
{
    [SerializeField]
    private QueueIndicator queueIndicator;

    [SerializeField]
    private TMPro.TextMeshProUGUI counterLabel;

    private void Update()
    {
        this.counterLabel.text = string.Format("{0}åè", queueIndicator.QueueLength);
    }
}
