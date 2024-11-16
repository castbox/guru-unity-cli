

using System.IO;

namespace Guru.SDK
{
    using System;
    using UnityEngine.UI;
    using System.Collections;
    using System.Collections.Generic;
    using UnityEngine;
    using UnityEditor; 
    
    
    /// <summary>
    /// Editor 菜单编辑器
    /// </summary>
    internal static class SDKInstallerEditorMenu
    {


#if GURU_SDK_DEV
        // TODO 显示开发功能窗口
#endif
        [MenuItem("Guru/SDK Installer", false, 1)]
        private static void OpenSDKInstallerWindow()
        {
            GuruSDKInstaller.CreateInstance<GuruSDKInstaller>().Show();
        }

    }
    
    
    /// <summary>
    /// Installer 编辑器窗体
    /// </summary>
    public class GuruSDKInstaller : EditorWindow
    {
        private const string VERSION = "1.0.0";
        private const string STATE_LOADING_VERSION_LIST = "loading_version_list";
        private const string STATE_VERSION_SELECTOR = "version_selector";


        private SDKVersionController _controller;
        private SDKVersionListDoc _versionListDoc;

        private string _curState;
        private int _curSDKIndex;
        private string _installedVersion;
        

        #region 启动

        private void OnEnable()
        {
            _curState = STATE_LOADING_VERSION_LIST;
            
            _controller = new SDKVersionController();
            _installedVersion = _controller.GetInstalledVersion();

            FetchOnlineVersionList();
        }
        

        #endregion

        #region Version List


        private void FetchOnlineVersionList()
        {
            _controller.FetchVersionList(OnGetVersionListSuccess, OnGetVersionListFailed);
        }


        /// <summary>
        /// 拉取 VersionList 成功
        /// </summary>
        /// <param name="doc"></param>
        private void OnGetVersionListSuccess(SDKVersionListDoc doc)
        {
            Debug.Log($"Success to get version list");
            _versionListDoc = doc;
            Debug.Log($"Latest version: {_versionListDoc.latest}");
            _curState = STATE_VERSION_SELECTOR;
            
            Repaint();
        }

        /// <summary>
        /// 拉取 VersionList 失败
        /// </summary>
        /// <param name="error"></param>
        private void OnGetVersionListFailed(string error)
        {
            Debug.LogError($"Failed to get version list");
            if (EditorUtility.DisplayDialog("下载失败", $"拉取版本信息失败:\n{error}", "重试一次", "关闭"))
            {
                FetchOnlineVersionList();
            }
            else
            {
                Close();
            }
        }


        #endregion
        
        #region GUI

        private void OnGUI()
        {
            DrawTitle();
            switch (_curState)
            {
                case STATE_LOADING_VERSION_LIST:
                    // Loading
                    DrawLoading();
                    break;
                
                case STATE_VERSION_SELECTOR:
                    // version selector
                    DrawSelector();
                    break;
                
            }
            
            
        }

        #endregion
        
        #region GUI Title

        private void DrawTitle()
        {
            var s = GetStyleBox();
            s.fontSize = 16;
            s.fixedHeight = 60;
            GUILayout.Label("GuruSDK Installer", s);
            
            s.fontSize = 12;
            s.fixedHeight = 24;
            GUILayout.Label($"ver {VERSION}", s);
            
            GUILayout.Space(2);
        }


        #endregion
        
        #region GUI Loading

        private void DrawLoading()
        {
            var s = GetStyleBox();
            s.fontSize = 12;
            s.fixedHeight = 40;
            GUILayout.Label("Loading...", s);
        }




        #endregion

        #region GUI Selector

        private void DrawSelector()
        {
            //---------------- 功能区域 --------------
            EditorLayoutHorizontal(() =>
            {
                GUIButton("更新SDK缓存", () =>
                {
                    // _manager.UpdateVersionList();
                });
                
                GUIButton("刷新列表", () =>
                {
                    _controller.UpdateVersionList(OnGetVersionListSuccess, OnGetVersionListFailed);
                    _curState = STATE_LOADING_VERSION_LIST;
                });
                
                GUIButton("Workspace", () =>
                {
                    _controller.OpenWorkspace();
                });
            }, new GUIStyle("box"));
            
            
            GUILayout.Space(4);

            var msg = string.IsNullOrEmpty(_installedVersion) ? "尚未安装" : _installedVersion;
            
            EditorGUILayout.LabelField("当前 SDK 版本", msg);
            
            GUILayout.Space(4);
            
            var verList = _controller.GetVersionNames();
            
            // var s = GetStyleLabelLv1();
            // EditorGUILayout.BeginHorizontal();
            GUILayout.Label("Select SDK Version");
            _curSDKIndex = EditorGUILayout.Popup(_curSDKIndex, verList);
            // EditorGUILayout.EndHorizontal();
            var verName = verList[_curSDKIndex];

            // Error: 版本不存在
            if (string.IsNullOrEmpty(verName))
            {
                GUILayout.Label("Unknown sdk version...");
                return;
            }
            
            // Error: 版本不在列表中
            var info = _controller.GetVersionInfo(verName);
            if (info == null)
            {
                GUILayout.Label($"Can't find version {verName}");
                return;
            }
            
            
            // 显示版本描述
            var s2 = GetStyleTextBox();
            EditorGUILayout.LabelField(info.desc, s2);
            
            // 如果 当前版本不是安装版本
            if (verName != _installedVersion)
            {
                
                GUILayout.Space(4);
                
                
                var sdkHome = _controller.GetSDKVersionHome(verName);
                if (Directory.Exists(sdkHome))
                {
                    // 如果本地有缓存
                    GUIButton($"安装【{verName}】全部依赖", () =>
                    {
                        _controller.RunInstallSDK(verName);
                    }, 40, Color.green);

                    DrawPackageMap(sdkHome);
                }
                else
                {
                    // 本地无缓存，需要在线拉取
                    GUIButton($"下载并安装【{verName}】全部依赖", () =>
                    {
                        _controller.RunInstallSDK(verName);
                    }, 40, Color.yellow);
                }

                
                
            }
        }


        /// <summary>
        /// 绘制包体信息
        /// </summary>
        private void DrawPackageMap(string sdkHome)
        {
            var path = Path.Combine(sdkHome, "sdk-config.json");
            if (!File.Exists(path))
            {
                GUILayout.Label("找不到版本配置，需要重新拉取");

                return;
            }
            
            var config = SDKConfigFile.Load(path);
            List<string> pkgs = new List<string>();
            foreach (var k in config.packages.Keys)
            {
                pkgs.Add(k);
            }
        }



        #endregion

        #region Draw PackageInfo

        private void DrawPackageInfoList(string version)
        {
            // var packages = _service.LoadPackageInfos(version);
        }



        #endregion
        
        #region GUI Utils

        private GUIStyle GetStyleBox()
        {
            var s = new GUIStyle("Box")
            {
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                fixedHeight = 40,
                alignment = TextAnchor.MiddleCenter,
                fixedWidth = position.width
            };

            return s;
        }


        private GUIStyle GetStyleLabelLv1()
        {
            var s = GetStyleBox();
            s.fontSize = 12;
            s.fixedHeight = 20;
            s.alignment = TextAnchor.MiddleLeft;
            return s;
        }


        private GUIStyle GetStyleTextBox()
        {
            var s = new GUIStyle("box")
            {
                alignment = TextAnchor.UpperLeft,
                clipping = TextClipping.Clip,
                fixedHeight = 80,
                fixedWidth = position.width
            };

            return s;
        }


        private void GUIButton(string label, Action onClick, int height = 0,  Color color = default)
        {
            Color _c = Color.white;
            if (color != default)
            {
                _c = GUI.color;
                GUI.color = color;
            }


            GUILayoutOption[] ops = null;
            if (height > 0)
            {
                ops = new GUILayoutOption[]
                {
                    GUILayout.Height(height)
                };
            }

            if (GUILayout.Button(label, ops))
            {
                onClick?.Invoke();
            }
            
            if (color != default)
            {
                GUI.color = _c;
            }
        }

        /// <summary>
        /// 水平布局
        /// </summary>
        /// <param name="onDrawing"></param>
        /// <param name="style"></param>
        private void EditorLayoutHorizontal(Action onDrawing, GUIStyle style = null)
        {
            EditorGUILayout.BeginHorizontal(style);
            onDrawing?.Invoke();
            EditorGUILayout.EndHorizontal();
        }


        #endregion
        
        
    }
    
}




