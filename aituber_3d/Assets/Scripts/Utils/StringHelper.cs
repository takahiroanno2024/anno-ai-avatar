using System.Collections.Generic;
using System.Linq;

namespace Aituber
{
    public class StringHelper

    {
        public static bool IsAlphanumeric(string input)
        {
            return input.All(char.IsLetterOrDigit);
        }

        public static bool ContainsAny(string text, List<string> words)
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
    }
}