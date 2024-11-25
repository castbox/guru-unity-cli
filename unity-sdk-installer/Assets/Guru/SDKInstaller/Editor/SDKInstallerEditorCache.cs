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
        public long ts; // 时间戳
        public string desc; // 版本描述
    }



    [Serializable]
    internal class SDKInstallerUserData
    {
        private static readonly string CacheRoot = Path.GetFullPath($"{Application.dataPath}/ProjectSettings");
        private const string FileName = "guru-sdk-installer.json";
        public string install_version; // 安装版本号
        public long install_ts; // 安装版本的时间戳

        /// <summary>
        /// 是否已有安装版本
        /// </summary>
        /// <returns></returns>
        public bool HasInstalled() => !string.IsNullOrEmpty(install_version) && install_ts == 0;

        /// <summary>
        /// 设置安装版本
        /// </summary>
        /// <param name="version"></param>
        /// <param name="timestamp"></param>
        public void SetInstallData(string version, long timestamp)
        {
            install_version = version;
            install_ts = timestamp;
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
            if (!Directory.Exists(CacheRoot))
            {
                Directory.CreateDirectory(CacheRoot);
            }

            File.WriteAllText(Path.Combine(CacheRoot, FileName), json);
        }


    }



}