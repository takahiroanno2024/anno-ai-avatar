using UnityEngine;
using UniVRM10;
using System.Collections;

namespace Aituber
{
    public class vrm10expressionchange : MonoBehaviour
    {
        [SerializeField] private Vrm10Instance vrmInstance;
        private Vrm10RuntimeExpression vrmRuntimeExpression;

        [SerializeField] private float blinkInterval = 3.0f; // 瞬きの間隔（秒）
        [SerializeField] private float blinkDuration = 0.1f; // 瞬きの持続時間（秒）

        private float nextBlinkTime = 0.0f; // 次の瞬きのタイミング

        void Start()
        {
            vrmRuntimeExpression = vrmInstance.Runtime.Expression;
        }

        void Update()
        {
            if (Time.time >= nextBlinkTime)
            {
                StartCoroutine(Blink());
                nextBlinkTime = Time.time + blinkInterval;
            }
        }

        IEnumerator Blink()
        {
            vrmRuntimeExpression.SetWeight(ExpressionKey.Blink, 1.0f);
            yield return new WaitForSeconds(blinkDuration);
            vrmRuntimeExpression.SetWeight(ExpressionKey.Blink, 0.0f);
        }
    }
}