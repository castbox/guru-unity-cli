namespace Guru.Editor
{
    using System;
    using System.IO;
    using UnityEditor;
    using UnityEngine;
    
    public class GuruSDKInstallManager
    {
        private const string UPM_HOME = ".upm";



        private const string SDK_CONFIG_JSON = "sdk_config.json";
        private static string ProjectPackageRoot = Path.GetFullPath($"{Application.dataPath}/../Packages");


        private SDKConfigFile _configFile;
        

        public GuruSDKInstallManager()
        {
            _configFile = SDKConfigFile.Load();
            if (_configFile == null)
            {

                throw new Exception("Can not found sdk-config.json file!!");
            }
        }
        


    }
}