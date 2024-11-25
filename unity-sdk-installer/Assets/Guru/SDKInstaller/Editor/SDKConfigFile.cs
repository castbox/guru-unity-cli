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
        public string desc;
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
        
        /// <summary>
        /// 获取当前的时间戳
        /// </summary>
        /// <returns></returns>
        private long GetCurrentTimestamp()
        {
            // 获取当前UTC时间
            DateTime currentTime = DateTime.UtcNow;
            // 转换为Unix时间戳（从1970年1月1日开始的秒数）
            TimeSpan elapsedTime = currentTime - new DateTime(1970, 1, 1);
            // 转换为长整型（秒级时间戳）
            long timestamp = (long)elapsedTime.TotalSeconds;
            return timestamp;
        }

        /// <summary>
        /// 获取发布日期
        /// </summary>
        /// <returns></returns>
        public DateTime GetDate()
        {
            if(string.IsNullOrEmpty(ts)) return DateTime.UtcNow;
            
            if(long.TryParse(ts, out long timestamp))
            {
                return TimestampToDate(timestamp);
            }

            return DateTime.UtcNow;
        }



        /// <summary>
        /// 
        /// </summary>
        /// <param name="timestamp"></param>
        /// <returns></returns>
        private DateTime TimestampToDate(long timestamp)
        {
            var startTime = new DateTime(1970, 1, 1);
            return startTime.AddSeconds(timestamp);
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