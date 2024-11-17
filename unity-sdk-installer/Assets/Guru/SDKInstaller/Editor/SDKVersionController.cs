


namespace Guru.SDK
{
    using System;
    using System.IO;
    using UnityEditor;
    using UnityEngine;
    using UnityEngine.Networking;
    using System.Collections.Generic;

    /// <summary>
    /// 版本管理服务
    /// </summary>
    public class SDKVersionController
    {
        private const string UPM_HOME = ".upm";
        private const string GURU_UNITY_CLI_NAME = "guru_unity_cli.py";
        private const string OSX_CMD_NAME = "cmd.command";
        private const string WIN_CMD_NAME = "cmd.bat";
        private const string ARGS_NAME = "args";
        private const string SDK_HOME = ".guru/unity";
        private const string SDK_LIB_NAME = "guru-sdk";
        
        private const string VERSION_LIST_URL =
            "https://raw.githubusercontent.com/castbox/unity-gurusdk-library/refs/heads/main/version_list.json";

        private static readonly string SDKLibraryHome = Path.Combine(GetOSUserHome(), $"{SDK_HOME}/{SDK_LIB_NAME}");
        
        private const string SDK_CONFIG_JSON = "sdk_config.json";
        private static readonly string ProjectPackages = Path.GetFullPath($"{Application.dataPath}/../Packages");

        private static readonly string Workspace =
            Path.GetFullPath($"{Application.dataPath}/../Library/guru-sdk-installer");

        private static readonly string VersionListDocPath = Path.GetFullPath($"{Workspace}/version_list.json");
        private static readonly string UnityProjectHome = Path.GetFullPath($"{Application.dataPath}/../");

        private string CmdName
        {
            get
            {
                var cmdName = OSX_CMD_NAME;
#if UNITY_EDITOR_WIN
                cmdName = WIN_CMD_NAME;
#endif
                return cmdName;
            }
        }

        private SDKConfigFile _configFile;
        private SDKVersionListDoc _versionList;
        private readonly SDKInstallerUserData _userData;
        private readonly string _pluginHome;

        public SDKVersionController()
        {
            _userData = SDKInstallerUserData.LoadOrCreate();
            _configFile = SDKConfigFile.Load();
            _pluginHome = GetPluginHome();
            EnsureWorkspace();
            // EnsureGuruCLIFile();
            EnsureCMDFile();

            Debug.Log($"Plugin Home: {_pluginHome}");
            Debug.Log($"Workspace: {Workspace}");
        }

        private void EnsureWorkspace()
        {
            if (!Directory.Exists(Workspace))
            {
                Directory.CreateDirectory(Workspace);
            }
        }

        #region Init

        private string GetPluginHome()
        {
            var guids = AssetDatabase.FindAssets($"{nameof(SDKVersionController)} t:script");
            if (guids.Length > 0)
            {
                var p = AssetDatabase.GUIDToAssetPath(guids[0]);
                return Path.GetFullPath(Directory.GetParent(p).Parent.FullName);
            }

            return $"{Application.dataPath}/Guru/SDKInstaller";
        }


        #endregion

        #region Version List


        /// <summary>
        /// 更新 Version 列表
        /// </summary>
        /// <param name="onSuccess"></param>
        /// <param name="onFailed"></param>
        public void UpdateVersionList(Action<SDKVersionListDoc> onSuccess, Action<string> onFailed = null)
        {
            TryCleanCachedVersionList();
            DownloadOnlineVersionList(onSuccess, onFailed);
        }


        /// <summary>
        /// 拉取线上的 Version List 文件
        /// </summary>
        public void FetchVersionList(Action<SDKVersionListDoc> onSuccess, Action<string> onFailed = null)
        {
            var cache_exists = TryLoadCachedVersionList(onSuccess);
            if (cache_exists)
                return;

            DownloadOnlineVersionList(onSuccess, onFailed);
        }


        private void DownloadOnlineVersionList(Action<SDKVersionListDoc> onSuccess, Action<string> onFailed = null)
        {
            var www = UnityWebRequest.Get(VERSION_LIST_URL);
            www.timeout = 30;
            www.SendWebRequest().completed += ao =>
            {
                if (www.result == UnityWebRequest.Result.Success)
                {
                    var doc = SDKVersionListDoc.Parse(www.downloadHandler.text);
                    SaveVersionListToCache(doc);
                    _versionList = doc;
                    onSuccess?.Invoke(doc);
                }
                else
                {
                    onFailed?.Invoke(www.error);
                }
            };
        }


        /// <summary>
        /// 尝试缓存 Version List
        /// </summary>
        /// <param name="onSuccess"></param>
        /// <returns></returns>
        private bool TryLoadCachedVersionList(Action<SDKVersionListDoc> onSuccess)
        {

            if (!File.Exists(VersionListDocPath))
                return false;

            var json = File.ReadAllText(VersionListDocPath);
            var doc = SDKVersionListDoc.Parse(json);
            if (doc == null)
                return false;

            var last_saved = DateTime.Parse(doc.last_saved);
            if ((DateTime.UtcNow - last_saved).TotalHours > 1)
            {
                return false; // 超过一小时以上，需要再次更新
            }

            _versionList = doc;
            onSuccess?.Invoke(doc);
            return true;
        }


        private void TryCleanCachedVersionList()
        {
            if (File.Exists(VersionListDocPath))
                File.Delete(VersionListDocPath);
        }

        private void SaveVersionListToCache(SDKVersionListDoc doc)
        {
            doc.last_saved = DateTime.UtcNow.ToString("g");
            doc.SaveToFile(VersionListDocPath);
        }


        /// <summary>
        /// 获取 Version 名称列表
        /// </summary>
        /// <returns></returns>
        public string[] GetVersionNames()
        {
            return _versionList?.GetVersionNames() ?? null;
        }


        public SDKVersionInfo GetVersionInfo(string versionName)
        {
            if (_versionList != null
                && _versionList.versions.TryGetValue(versionName, out var info))
            {
                return info;
            }

            return null;
        }



        #endregion

        #region Packages

        // 获取包体信息
        public Dictionary<string, GuruPackageInfo> GetPackages() => _configFile?.packages ?? null;

        #endregion

        #region UserData




        /// <summary>
        /// 获取安装版本
        /// </summary>
        /// <returns></returns>
        public string GetInstalledVersion()
        {
            return _userData.install_version;
        }

        /// <summary>
        /// 设置安装版本
        /// </summary>
        /// <param name="version"></param>
        public void SetInstalledVersion(string version)
        {
            _userData.SetInstallVersion(version);
        }



        #endregion

        #region IO

        private void OpenPath(string path)
        {
#if UNITY_EDITOR_OSX
            EditorUtility.RevealInFinder(path);
            return;
#endif
            
            Application.OpenURL($"file://{path}");
        }


        public void OpenWorkspace()
        {
            OpenPath(Workspace);
        }

        public static string GetOSUserHome()
        {
            return Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        }


        public bool IsSDKHomeExists()
        {
            return Directory.Exists(SDKLibraryHome);
        }

        /// <summary>
        /// 获取某个 SDK 版本的路径
        /// </summary>
        /// <param name="version"></param>
        /// <returns></returns>
        public string GetSDKVersionHome(string version)
        {
            var path = Path.Combine(SDKLibraryHome, version);
            return path;
        }



        #endregion

        #region CMD

        private void EnsureGuruCLIFile()
        {

            string userHome = GetOSUserHome();
            string guruHome = Path.Combine(userHome, $".guru/unity");

            if (!Directory.Exists(guruHome))
            {
                UnityEngine.Windows.Directory.CreateDirectory(guruHome);
            }
            
            string to = Path.Combine(guruHome, GURU_UNITY_CLI_NAME);
            if(File.Exists(to)) return;
            var from = Path.Combine(_pluginHome, $"File/{GURU_UNITY_CLI_NAME}");
            File.Copy(from, to);
        }


        private void EnsureCMDFile()
        {
            string from = Path.Combine(_pluginHome, $"File/{CmdName}");
            string to = Path.Combine(Workspace, CmdName);

            if (File.Exists(to)) return;
            File.Copy(from, to);
        }


        public void RunCmd()
        {
            var cmdPath = Path.Combine(Workspace, CmdName);
            if(!File.Exists(cmdPath)) EnsureCMDFile();
            Application.OpenURL($"file://{cmdPath}");
        }


        /// <summary>
        /// 运行安装命令
        /// </summary>
        /// <param name="versionName"></param>
        public void RunInstallSDK(string versionName)
        {
            // 写入文件命令
            WriteCMDArgs(new Dictionary<string, string>()
            {
                {"RUN_MODE", "install"} ,
                {"PROJECT", UnityProjectHome},
                {"VERSION", versionName},
            });
            // 执行脚本
            RunCmd();
        }


        private void WriteCMDArgs(Dictionary<string, string> args)
        {
            List<string> lines = new List<string>(args.Count);
            string filePath = Path.Combine(Workspace, ARGS_NAME);
            foreach (var kvp in args)
            {
#if UNITY_EDITOR_OSX
                lines.Add($"export {kvp.Key}={kvp.Value}");
#elif UNITY_EDITOR_WIN
                lines.Add($"set {kvp.Key}={kvp.Value}");
                filePath = Path.Combine(Workspace, $"{ARGS_NAME}.bat");
#endif
            }
            File.WriteAllLines(filePath, lines);
        }





        #endregion
    }
}