using UnityEngine;
using UnityEngine.UI;
using Cinemachine;

namespace Aituber
{
    public class CameraSwitcher : MonoBehaviour
    {
        public CinemachineVirtualCamera camera1;
        public CinemachineVirtualCamera camera2;
        public Button switchCameraButton;

        void Start()
        {
            switchCameraButton.onClick.AddListener(ChangeCamera); // ボタンにリスナーを追加
        }

        public void ChangeCamera()
        {
            // カメラ1とカメラ2の優先順位を入れ替える
            int temp = camera1.Priority;
            camera1.Priority = camera2.Priority;
            camera2.Priority = temp;
        }

        public void ChangeCameraTo1()
        {
            // カメラ1優先
            camera1.Priority = 10;
            camera2.Priority = 5;
        }

        public void ChangeCameraTo2()
        {
            // カメラ1優先
            camera1.Priority = 5;
            camera2.Priority = 10;
        }
    }
}