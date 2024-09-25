using System.Collections.Generic;
using System.Text;

namespace Aituber
{
    public class KanaConverter
    {
        private static readonly Dictionary<char, char> halfWidthToFullWidthKanaMap = new Dictionary<char, char>
        {
            { 'ｱ', 'ア' }, { 'ｲ', 'イ' }, { 'ｳ', 'ウ' }, { 'ｴ', 'エ' }, { 'ｵ', 'オ' },
            { 'ｶ', 'カ' }, { 'ｷ', 'キ' }, { 'ｸ', 'ク' }, { 'ｹ', 'ケ' }, { 'ｺ', 'コ' },
            { 'ｻ', 'サ' }, { 'ｼ', 'シ' }, { 'ｽ', 'ス' }, { 'ｾ', 'セ' }, { 'ｿ', 'ソ' },
            { 'ﾀ', 'タ' }, { 'ﾁ', 'チ' }, { 'ﾂ', 'ツ' }, { 'ﾃ', 'テ' }, { 'ﾄ', 'ト' },
            { 'ﾅ', 'ナ' }, { 'ﾆ', 'ニ' }, { 'ﾇ', 'ヌ' }, { 'ﾈ', 'ネ' }, { 'ﾉ', 'ノ' },
            { 'ﾊ', 'ハ' }, { 'ﾋ', 'ヒ' }, { 'ﾌ', 'フ' }, { 'ﾍ', 'ヘ' }, { 'ﾎ', 'ホ' },
            { 'ﾏ', 'マ' }, { 'ﾐ', 'ミ' }, { 'ﾑ', 'ム' }, { 'ﾒ', 'メ' }, { 'ﾓ', 'モ' },
            { 'ﾔ', 'ヤ' }, { 'ﾕ', 'ユ' }, { 'ﾖ', 'ヨ' },
            { 'ﾗ', 'ラ' }, { 'ﾘ', 'リ' }, { 'ﾙ', 'ル' }, { 'ﾚ', 'レ' }, { 'ﾛ', 'ロ' },
            { 'ﾜ', 'ワ' }, { 'ｦ', 'ヲ' }, { 'ﾝ', 'ン' },
            { 'ｧ', 'ァ' }, { 'ｨ', 'ィ' }, { 'ｩ', 'ゥ' }, { 'ｪ', 'ェ' }, { 'ｫ', 'ォ' },
            { 'ｬ', 'ャ' }, { 'ｭ', 'ュ' }, { 'ｮ', 'ョ' }, { 'ｯ', 'ッ' },
            { 'ﾞ', '゛' }, { 'ﾟ', '゜' },
            { 'ｰ', 'ー' }, { '｡', '。' }, { '｢', '「' }, { '｣', '」' }, { '､', '、' }, { '･', '・' }
        };

        public static string ConvertHalfWidthToFullWidthKana(string input)
        {
            StringBuilder sb = new StringBuilder();

            foreach (char c in input)
            {
                if (halfWidthToFullWidthKanaMap.ContainsKey(c))
                {
                    sb.Append(halfWidthToFullWidthKanaMap[c]);
                }
                else
                {
                    sb.Append(c);
                }
            }

            return sb.ToString();
        }
    }
}