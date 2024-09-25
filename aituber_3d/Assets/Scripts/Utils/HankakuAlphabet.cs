namespace Aituber
{
    public static class HankakuAlphabet
    {
        // 全角アルファベットから半角アルファベットに変換する静的関数
        public static string ConvertZenkakuToHankaku(string input)
        {
            if (input == null) return null;

            char[] chars = input.ToCharArray();

            for (int i = 0; i < chars.Length; i++)
            {
                // 全角大文字アルファベットを半角大文字アルファベットに変換
                if (chars[i] >= '\uFF21' && chars[i] <= '\uFF3A')
                {
                    chars[i] = (char)(chars[i] - '\uFF21' + 'A');
                }
                // 全角小文字アルファベットを半角小文字アルファベットに変換
                else if (chars[i] >= '\uFF41' && chars[i] <= '\uFF5A')
                {
                    chars[i] = (char)(chars[i] - '\uFF41' + 'a');
                }
            }

            return new string(chars);
        }
    }
}