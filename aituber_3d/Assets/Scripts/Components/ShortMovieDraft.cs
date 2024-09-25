using System;
using System.Collections.Generic;
using Aituber;
using UnityEngine;

namespace ShortMovie
{
    public class ShortMovieDraft : MonoBehaviour
    {
        [SerializeField] private List<DraftItem> draftItems;

        public List<DraftItem> GetDraftItems()
        {
            return draftItems;
        }
    }

    public class ShortMovieDraftWithAudio
    {
        public readonly List<Tuple<DraftItem, AudioClip>> draftItems;

        public ShortMovieDraftWithAudio(List<Tuple<DraftItem, AudioClip>> draftItems)
        {
            this.draftItems = draftItems;
        }
    }

    [System.Serializable]
    public class DraftItem
    {
        [SerializeField] [TextArea(1, 3)] public string text;
        [SerializeField] public MotionType motionType = MotionType.Idle;
    }
}