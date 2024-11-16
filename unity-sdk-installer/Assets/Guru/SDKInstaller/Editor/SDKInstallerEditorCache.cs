namespace Guru.SDK
{
    using System;
    using System.Collections.Generic;
    using UnityEngine;
    using System.IO;
    using System.Linq;
    using LitJson;
    
    /// <summary>
    /// SDK 版本列表
    /// </summary>
    [Serializable]
    public class SDKVersionListDoc
    {
        public string last_saved;
        public string latest;
        public Dictionary<string, SDKVersionInfo> versions;

        public static SDKVersionListDoc LoadFromFile(string filePath)
        {
            if (File.Exists(filePath))
            {
                var json = File.ReadAllText(filePath);
                return Parse(json);
            }

            return null;
        }
        
        
        /// <summary>
        /// 解析 JSON
        /// </summary>
        /// <param name="json"></param>
        /// <returns></returns>
        public static SDKVersionListDoc Parse(string json)
        {
            return JsonMapper.ToObject<SDKVersionListDoc>(json);
        }
        
        /// <summary>
        /// 保存至文件
        /// </summary>
        /// <param name="filePath"></param>
        public void SaveToFile(string filePath)
        {
            var wt = new JsonWriter() { IndentValue = 1 };
            JsonMapper.ToJson(this, wt);
            File.WriteAllText(filePath, wt.ToString());
        }


        public string[] GetVersionNames()
        {
            var nameList = versions.Keys.ToList();
            nameList.Sort();

            return nameList.ToArray();
        }

    }

    /// <summary>
    /// SDK 版本信息
    /// </summary>
    [Serializable]
    public class SDKVersionInfo
    {
        public int ts;
        public string desc;
    }



    [Serializable]
    internal class SDKInstallerUserData
    {
        private static readonly string CacheRoot = Path.GetFullPath($"{Application.dataPath}/ProjectSettings");
        private const string FileName = "guru-sdk-installer.json";


        public string install_version;
        public string install_date;

        /// <summary>
        /// 是否已有安装版本
        /// </summary>
        /// <returns></returns>
        public bool HasInstalled() => !string.IsNullOrEmpty(install_version) && !string.IsNullOrEmpty(install_date);

        /// <summary>
        /// 设置安装版本
        /// </summary>
        /// <param name="version"></param>
        public void SetInstallVersion(string version)
        {
            install_version = version;
            install_date = DateTime.UtcNow.ToString("g");
            Save();
        }

        public static SDKInstallerUserData LoadOrCreate()
        {
            var path = Path.Combine(CacheRoot, FileName);
            if (File.Exists(path))
            {
                var json = File.ReadAllText(path);
                return JsonMapper.ToObject<SDKInstallerUserData>(json);
            }

            return new SDKInstallerUserData();
        }


        public void Save()
        {
            var json = JsonMapper.ToJson(this);
            File.WriteAllText(Path.Combine(CacheRoot, FileName), json);
        }


    }



}