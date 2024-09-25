using System;

namespace Aituber
{
    public static class SharedData
    {
        public static string SelectedComment = "";
        public static event Action OnCommentSelected;

        public static void SelectComment(string comment)
        {
            SelectedComment = comment;
            OnCommentSelected?.Invoke();
        }
    }
}