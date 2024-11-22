using LitJson;

namespace Guru.SDK
{
    using System;
    using System.Collections.Generic;
    using System.IO;
    using UnityEngine;
    
    
    [Serializable]
    public class SDKConfigFile
    {
        private const string CONFIG_FILE_NAME = "sdk-config.json";
        
        public string version; // SDK 版本号
        public string ts;
        public Dictionary<string, GuruPackageInfo> packages; // 包列表
        
        private static string FilePath => Path.GetFullPath($"{Application.dataPath}/../Packages/{CONFIG_FILE_NAME}");

        public static SDKConfigFile Load(string path = "")
        {
            if(string.IsNullOrEmpty(path)) path = FilePath;
            if (File.Exists(path))
            {
                return JsonMapper.ToObject<SDKConfigFile>(File.ReadAllText(path)); // JsonUtility.FromJson<>()
                // return JsonConvert.DeserializeObject<SDKConfigFile>(File.ReadAllText(path));
            }
            
            Debug.LogWarning("Can not found config file: {path}");
            return null;
        }
    }
    
    /*
     * "com.guru.unity.sdk": {
            "group": ["guru-sdk"],
            "type": 0,
            "dependencies": [
              "*guru-sdk"
            ]
          },
     *
     */
    [Serializable]
    public class GuruPackageInfo
    {
        public string group;
        public bool embedded;
        public List<string> dependencies;
    }

}