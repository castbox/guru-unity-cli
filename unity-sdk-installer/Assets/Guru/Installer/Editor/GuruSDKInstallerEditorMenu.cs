namespace Guru.Editor
{
    using UnityEditor;
    
    
    public class GuruSDKInstallerEditorMenu
    {


#if GURU_SDK_DEV
       // TODO 显示开发功能窗口
#endif
        [MenuItem("Guru/SDK/Installer", false, 1)]
        private static void OpenSDKInstallerWindow()
        {
            
        }



    }
}