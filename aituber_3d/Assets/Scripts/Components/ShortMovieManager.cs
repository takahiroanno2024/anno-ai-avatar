using System;
using System.Linq;
using Aituber;
using Cysharp.Threading.Tasks;
using ShortMovie;
using UnityEngine;

public class ShortMovieManager : MonoBehaviour
{
    [SerializeField] private ShortMovieDraft draft;
    [SerializeField] private TextToSpeech tts;
    [SerializeField] private RandomAnimation1 anim;

    async void Start()
    {
        foreach (var _ in Enumerable.Range(1, 10).ToList())
        {
            await PlayDraft();
        }
    }

    async UniTask PlayDraft()
    {
        var prepareDraft = await PrepareDraft();
        foreach (var (item, clip) in prepareDraft.draftItems)
        {
            await HandleDraftItem(clip, item);
        }

        anim.SetAnimation(MotionType.Idle);
    }

    private async UniTask HandleDraftItem(AudioClip clip, DraftItem item)
    {
        anim.SetAnimation(item.motionType);
        await tts.PlayAudio(tts.annoAudioSource,clip, item.text,1f);
    }

    async UniTask<ShortMovieDraftWithAudio> PrepareDraft()
    {
        var draftItems = draft.GetDraftItems();
        var tasks = Enumerable.Select(draftItems, draftItem => tts.DownloadAudio(draftItem.text,"v2"));
        var clips = await UniTask.WhenAll(tasks);
        var pairs = draftItems.Zip(clips, (item, clip) => new Tuple<DraftItem, AudioClip>(item, clip)).ToList();

        return new ShortMovieDraftWithAudio(pairs);
    }
}