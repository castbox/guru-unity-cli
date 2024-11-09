using System;

namespace Guru.Editor
{
    using System.Collections;
    using System.Collections.Generic;
    using UnityEngine;
    using UnityEditor; 
    
    
    public class GuruSDKInstaller : EditorWindow
    {





        private GuruSDKInstallManager _manager;
        


        #region 启动

        private void OnEnable()
        {
            _manager = new GuruSDKInstallManager();
        }

        #endregion


        #region GUI

        private void OnGUI()
        {
            
            
            
            
        }

        #endregion
        
        
        
    }
    
}




