#!/usr/bin/env python3

import argparse
import os
import shutil
import json
import datetime
from os.path import expanduser

# CONSTS
VERSION = '0.1.0'
SDK_CONFIG_JSON = 'sdk-config.json'  # SDK 开发者定义的 upm 包的配置关系，包含所有包体的可选以及从属关系, [需要配置在 DEV 项目]
GURU_PKGS = 'guru-pkgs'  # SDK 开发者定义的 upm 包列表，用于标记从 dev 项目中需要拾取的包有哪些, [需要配置在 DEV 项目]
SDK_HOME_NAME = '.guru/unity/guru-sdk'  # 用户设备上缓存 SDK 各个版本的路径
SDK_LIB_REPO = 'git@github.com:castbox/unity-gurusdk-library.git'  # 线上发布的 SDK 静态库的 repo
SDK_DEV_REPO = 'git@github.com:castbox/unity-gurusdk-dev.git'  # SDK 开发者所使用的开发 Repo
UPM_ROOT_NAME = '.upm'  # 在用户的项目中 Packages 路径下需要建立的文件夹名称
UNITY_MANIFEST_JSON = 'manifest.json'  # unity 项目自身的 UPM 包清单文件
UNITY_PACKAGES_LOCK_JSON = 'packages-lock.json'  # unity 项目自身的 UPM 包清单文件
UNITY_PACKAGES_ROOT = 'Packages'  # unity 项目自身的 UPM 包清单文件
UNITY_DEV_PROJECT = 'GuruSDKDev'  # unity 开发项目中 Unity 工程路径的二级目录


__user_sdk_home: str = ''

# ---------------------- UTILS ----------------------
# call cmd
def run_cmd(cmdline: str,
            work_path: str = '',
            show_log: bool = True):
    if len(work_path) > 0:
        os.chdir(work_path)
    if show_log:
        log = os.popen(cmdline).read()
        print(log)
    else:
        os.popen(cmdline)


# delete full dir
def delete_dir(dir_path:str):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    else:
        print('dir is not exist:', dir_path)
    pass


# make the dir path if it not exists
def ensure_dir(dir_path: str):
    if os.path.exists(dir_path):
        return

    os.mkdir(dir_path)


def get_user_home():
    return expanduser("~")


# get the local path of sdk_home
def get_sdk_home():
    global __user_sdk_home
    if len(__user_sdk_home) == 0:
        __user_sdk_home = os.path.join(get_user_home(), SDK_HOME_NAME)

    if is_windows_platform():
        __user_sdk_home = __user_sdk_home.replace('/', '\\')

    return __user_sdk_home


def is_windows_platform():
    return os.name == 'nt'


# ---------------------- SYNC ----------------------
# download latest sdk
def sync_sdk():
    sdk_home = get_sdk_home()

    if os.path.exists(sdk_home):
        # remove old files
        delete_dir(sdk_home)
        pass

    os.makedirs(sdk_home)
    run_cmd(f'git clone --depth 1 {SDK_LIB_REPO} .', sdk_home)
    pass


# sync latest sdk repo to the path '~/.guru/unity/guru-sdk'
def sync_and_install_sdk(unity_proj_path: str):

    sdk_home = get_sdk_home()
    upm_root = os.path.join(unity_proj_path, f'{UNITY_PACKAGES_ROOT}/{UPM_ROOT_NAME}')
    manifest_path = os.path.join(unity_proj_path, f'{UNITY_PACKAGES_ROOT}/{UNITY_MANIFEST_JSON}')
    guru_pkgs = os.path.join(unity_proj_path, f'{UNITY_PACKAGES_ROOT}/{GURU_PKGS}')

    if not os.path.exists(guru_pkgs):
        print("user has not choose any package yet, no packages will be install")
        return
        pass

    # clean old sdk files
    if os.path.exists(upm_root):
        delete_dir(upm_root)

    # re-make .upm dir
    ensure_dir(upm_root)

    manifest_json = load_unity_manifest_json(manifest_path)
    if manifest_json is None:
        return

    with open(guru_pkgs, 'r') as f:
        lines = f.readlines()
        for p in lines:
            if '#' in p:
                # comment line
                continue

            in_path = os.path.join(sdk_home, p)
            if not os.path.exists(in_path):
                print(f'package [{p}] not found, skip install...')
                continue

            run_cmd(f'ln -s {in_path} {p}', upm_root)
            print('Add package at path: ', in_path)

            manifest_json['dependencies'][p] = f'file:{UPM_ROOT_NAME}/{p}'

            # save the manifest file
            save_unity_manifest_json(manifest_path, manifest_json)
            pass
        pass
    pass


# load manifest.json -> jsonObject
def load_unity_manifest_json(path: str):
    with open(path, 'r') as f:
        manifest_json = json.loads(f.read())
        if manifest_json is None:
            print(f'[{path}] not found... install failed!')
            return None
        pass
        f.close()
        return manifest_json


# save jsonObject -> manifest.json
def save_unity_manifest_json(path: str, data: object):
    with open(path, 'w') as f:
        json_str = json.dumps(data)
        f.write(json_str)
        f.close()
    pass


# ---------------------- PUBLISH ----------------------
# publish the new version
def publish_guru_sdk(version: str, branch: str):

    source, output, to_path = download_all_repos_and_gen_path(version, branch)

    pkg_path = os.path.join(source, 'packages')

    # clone all remote upms
    collect_all_upm_packages(source)

    # make version dir
    shutil.copytree(pkg_path, to_path)

    push_msg = f'Make version {version} on  {datetime.date.today().strftime("%Y/%m/%d %H:%M:%S")}  by push'

    # commit to the publishing repo
    run_cmd(f'git add .', output)
    run_cmd(f'git commit -m \"{push_msg}\"', output)
    run_cmd(f'git push', output)

    print('===== Publish is done! ======')

    delete_dir(source)
    delete_dir(output)

    pass


# download the source proj 'unity-gurusdk-dev'
# and the output proj 'unity-gurusdk-library'
def download_all_repos_and_gen_path(version: str, branch: str):
    pwd = os.getcwd()
    print('cmd path:', pwd)

    source = os.path.join(pwd, 'source')
    output = os.path.join(pwd, 'output')
    to_path = os.path.join(output, version)

    if is_windows_platform():
        source = source.replace('/', '\\')
        output = output.replace('/', '\\')
        to_path = to_path.replace('/', '\\')


    # clear source from last pull
    if os.path.exists(source):
        print('clear source at', source)
        delete_dir(source)

    # clear temp lib dir
    if os.path.exists(output):
        print('clear output at', output)
        delete_dir(output)

    # clear same version and will make a new version folder
    if os.path.exists(to_path):
        print('clear to_path at', to_path)
        delete_dir(to_path)

    # default branch
    if len(branch) == 0:
        branch = 'main'

    # clone dev
    print('create source at', source)
    os.makedirs(source)
    run_cmd(f'git clone -b {branch} {SDK_DEV_REPO} .', source)
    run_cmd(f'git submodule update --init --recursive', source)

    # clone lib
    print('create output at', output)
    os.makedirs(output)
    run_cmd(f'git clone {SDK_LIB_REPO} .', output)

    return source, output, to_path

    pass


# collect call upm files from dev_project，
# and collect them into ‘dev_project/packages’ path
# all ump repos from GitHub will be cloned
def collect_all_upm_packages(root_path: str):

    sdk_upm_home = os.path.join(root_path, 'packages')
    unity_proj_path = os.path.join(root_path, UNITY_DEV_PROJECT)
    packages_path = os.path.join(unity_proj_path, UNITY_PACKAGES_ROOT)
    # manifest_file = os.path.join(packages_path, "manifest.json")
    lock_file = os.path.join(packages_path, UNITY_PACKAGES_LOCK_JSON)
    config_file = os.path.join(packages_path, SDK_CONFIG_JSON)

    if not os.path.exists(config_file):
        print('can not found <sdk-config>', config_file)
        return None

    if not os.path.exists(lock_file):
        print('can not found <packages-lock>', lock_file)
        return None

    with open(lock_file, 'r') as f1:
        lock_data = json.loads(f1.read())

    # with open(config_file, 'r') as f2:
    #     sdk_config = json.dumps(f2.read())
    #     print('sdk-config', sdk_config)

        for pkg_id in lock_data['dependencies']:

            item = lock_data['dependencies'][pkg_id]

            if item is None:
                continue

            if item['source'] == 'git':
                # git upm
                # hash = item['hash']
                git_url = item['version']
                to_path = os.path.join(sdk_upm_home, pkg_id)

                if not os.path.exists(to_path):
                    os.mkdir(to_path)

                if '#' in git_url:
                    raw = git_url.split('#')
                    git_url = raw[0]
                    tag = raw[1]
                    sc = f'git clone -b {tag} --depth 1 {git_url} .'
                else:
                    sc = f'git clone --depth 1 {git_url} .'

                # clone
                run_cmd(sc, to_path)

                pass
            pass
        run_cmd(f"cp {config_file} {os.path.join(sdk_upm_home, SDK_CONFIG_JSON)}")
        pass
    pass


# init all the args from input
def init_args():
    parser = argparse.ArgumentParser(description='guru-sdk cli tool')
    parser.add_argument('action', type=str, help='sync,publish,debug_source')
    parser.add_argument('--version', type=str, help='version for publish')
    parser.add_argument('--branch', type=str, help='branch for dev project')
    return parser.parse_args()


# Entry of the cli.
if __name__ == '__main__':
    print(f'========== Welcome to GuruSdk CLI [{VERSION}] ==========')
    args = init_args()
    print('OS', os.name)
    print('Action:', args.action)

    action = args.action
    version = args.version
    branch = args.branch

    if action == 'sync':
        # sync the latest version of guru_sdk
        sync_sdk()
    elif action == 'publish':
        # publish sdk with special version
        if len(version) == 0:
            print('wrong version format')
        elif len(branch) == 0:
            print('wrong branch name')
        else:
            publish_guru_sdk(version, branch)

    elif action == 'debug_source':
        if len(version) == 0:
            print('wrong version format')
        elif len(branch) == 0:
            print('wrong branch name')
        else:
            download_all_repos_and_gen_path(version, branch)

    pass
