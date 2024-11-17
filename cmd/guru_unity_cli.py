#! /usr/bin/python3
# coding=utf-8

import argparse
import os
import shutil
import json
import datetime
from os.path import expanduser

# CONSTS
VERSION = '0.4.0'
SDK_CONFIG_JSON = 'sdk-config.json'  # SDK 开发者定义的 upm 包的配置关系，包含所有包体的可选以及从属关系, [需要配置在 DEV 项目]
SDK_HOME_NAME = '.guru/unity/guru-sdk'  # 用户设备上缓存 SDK 各个版本的路径
SDK_LIB_REPO = 'git@github.com:castbox/unity-gurusdk-library.git'  # 线上发布的 SDK 静态库的 repo
SDK_DEV_REPO = 'git@github.com:castbox/unity-gurusdk-dev.git'  # SDK 开发者所使用的开发 Repo
UPM_ROOT_NAME = '.upm'  # 在用户的项目中 Packages 路径下需要建立的文件夹名称
UNITY_MANIFEST_JSON = 'manifest.json'  # unity 项目自身的 UPM 包清单文件
UNITY_PACKAGES_LOCK_JSON = 'packages-lock.json'  # unity 项目自身的 UPM 包清单文件
UNITY_PACKAGES_ROOT = 'Packages'  # unity 项目自身的 UPM 包清单文件
UNITY_DEV_PROJECT = 'GuruSDKDev'  # unity 开发项目中 Unity 工程路径的二级目录
VERSION_LIST = 'version_list.json'  # SDK 版本描述文件
LOG_TXT = 'log.txt'

ERROR_UNITY_PROJECT_NOT_FOUND = 100
ERROR_WRONG_VERSION = 101
ERROR_WRONG_SOURCE_PATH = 102
ERROR_SDK_CONFIG_NOT_FOUND = 103

__user_sdk_home: str = ''
global __cur_dir


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
def delete_dir(dir_path: str):
    if os.path.exists(dir_path):
        if is_windows_platform():
            run_cmd(f'rd /s /q {dir_path}')
        else:
            shutil.rmtree(dir_path)
    else:
        print('dir is not exist:', dir_path)
    pass


# make the dir path if it not exists
def ensure_dir(dir_path: str):
    if os.path.exists(dir_path):
        return

    os.makedirs(dir_path)


def get_user_home():
    return expanduser("~")


# get the local path of sdk_home
def get_sdk_home():
    global __user_sdk_home

    if len(__user_sdk_home) > 0 and os.path.exists(__user_sdk_home):
        return __user_sdk_home

    __user_sdk_home = to_safe_path(f'{get_user_home()}/{SDK_HOME_NAME}')

    return __user_sdk_home


# check is running on windows sys
def is_windows_platform():
    return os.name == 'nt'

def is_str_empty(txt: str):
    if txt is None:
        return True

    if len(txt) == 0:
        return True

    return False

def path_join(path1: str, path2: str):
    p = os.path.join(path1, path2)
    return to_safe_path(p)


def to_safe_path(path: str):
    if is_windows_platform():
        return path.replace('/', '\\')  # windows os
    return path.replace('\\', '/')  # mac or liunx os


# read content from a file
def read_file(path: str):
    if not os.path.exists(path):
        print('file not found', path)
        return ''

    with open(path, 'r') as f:
        txt = f.read()
        f.close()
        return txt


# write sth into a file
def write_file(path: str, content: str):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        f.close()


def output_log_txt(txt: str):
    path = f'{__cur_dir}/{LOG_TXT}'
    write_file(path, txt)


def output_success(content: str):
    if is_str_empty(content):
        content = '...'

    txt = f'success for {content}'
    output_log_txt(txt)


# ---------------------- SYNC ----------------------
# sync and install sdk from local cache
def sync_and_install_sdk(unity_proj: str, version: str):
    sdk_home = get_sdk_home()
    version_dir = path_join(sdk_home, version)

    if not os.path.exists(sdk_home):
        sync_sdk()

    if not os.path.exists(version_dir):
        sync_sdk()

    install_sdk(unity_proj, version)
    pass


# download latest sdk
def sync_sdk():
    sdk_home = get_sdk_home()

    # only support for quick clone, so every time it will remove all files, then clone it again
    if os.path.exists(sdk_home):
        # remove old files
        delete_dir(sdk_home)
        pass

    os.makedirs(sdk_home)
    run_cmd(f'git clone --depth 1 {SDK_LIB_REPO} .', sdk_home)
    output_success('sync complete')
    pass


# sync latest sdk repo to the path '~/.guru/unity/guru-sdk'
def install_sdk(unity_proj_path: str, version: str):

    sdk_home = get_sdk_home()
    version_home = path_join(sdk_home, version)
    upm_root = path_join(unity_proj_path, f'{UNITY_PACKAGES_ROOT}/{UPM_ROOT_NAME}')
    manifest_path = path_join(unity_proj_path, f'{UNITY_PACKAGES_ROOT}/{UNITY_MANIFEST_JSON}')
    sdk_config = path_join(version_home, SDK_CONFIG_JSON)

    if not os.path.exists(sdk_config):
        print(f'sdk-config not found:: \n{sdk_config}')
        exit(ERROR_SDK_CONFIG_NOT_FOUND)
        pass

    # clean old sdk files
    if os.path.exists(upm_root):
        delete_dir(upm_root)
    # re-make .upm dir
    ensure_dir(upm_root)

    manifest_json = load_unity_manifest_json(manifest_path)
    if manifest_json is None:
        return

    # install all packages from sdk-config
    with open(sdk_config, 'r', encoding='utf-8') as f:
        txt = f.read()
        print(txt)

        cfg = json.loads(txt)

        if cfg is None or cfg['packages'] is None:
            print('json parse error with', sdk_config, 'plz fix the errors')
            return

        for p in cfg['packages']:
            in_path = path_join(version_home, p)
            if not os.path.exists(in_path):
                print(f'package [{p}] not found, skip install...')
                continue

            print('Add package at path: ', in_path)
            make_softlink(in_path, p, upm_root)

            # record deps
            manifest_json['dependencies'][p] = f'file:{UPM_ROOT_NAME}/{p}'
            pass
        # save the manifest file
        save_unity_manifest_json(manifest_path, manifest_json)
        pass
    pass

    output_success('install complete')


# create softlink with os cmd
def make_softlink(source_path: str, link_name: str, dest_dir: str):
    if is_windows_platform():
        # run_cmd(f'mklink /D {dest_dir}\\{link_name} {source_path}')
        os.symlink(source_path, f'{dest_dir}/{link_name}')
        pass
    else:
        run_cmd(f'ln -s {source_path} {link_name}', dest_dir)
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
def _publish_sdk(source: str, output: str, clean_mode: int = 0):

    # clone all remote upms
    _version, additions = collect_upm_dependencies_and_version(source)

    # sub paths
    to_path = path_join(output, _version)
    pkg_path = path_join(source, 'packages')

    # make version dir
    if os.path.exists(to_path):
        delete_dir(to_path)
    shutil.copytree(pkg_path, to_path)

    # update version list
    update_version_list(to_path, output)

    push_msg = f'Make version {_version} on  {datetime.date.today().strftime("%Y/%m/%d %H:%M:%S")}  by push'

    # commit to the publishing repo
    run_cmd(f'git add .', output)
    run_cmd(f'git commit -m \"{push_msg}\"', output)
    run_cmd(f'git push', output)

    print('===== Publish is done! ======')

    if clean_mode == 1:
        delete_dir(source)
        delete_dir(output)
    elif clean_mode == 2:
        for p in additions:
            delete_dir(p)
            pass
    pass


# publish sdk vai cil or jenkins
def publish_sdk_by_cli(publish_branch: str):
    source = download_source_repo(publish_branch)
    output = download_output_repo()
    _publish_sdk(source, output, 1)
    pass


# publish sdk from local cmd from unity project
def publish_sdk_by_unity(unity_project: str):
    source = unity_project
    output = download_output_repo()
    _publish_sdk(source, output, 2)
    pass


# download unity-gurusdk-dev repo to dest path ( the default pull_branch is 'main' )
def download_source_repo(pull_branch: str = ''):
    dest = path_join(__cur_dir, 'source')

    # clear source from last pull
    if os.path.exists(dest):
        print('clear source at', dest)
        delete_dir(dest)

    if len(pull_branch) == 0:
        pull_branch = 'main'

    print('create source at', dest)
    os.makedirs(dest)
    run_cmd(f'git clone -b {pull_branch} --depth=1 {SDK_DEV_REPO} .', dest)
    run_cmd(f'git submodule update --init --recursive', dest)

    return dest
    pass


# download unity-gurusdk-library repo to dest path ( the default pull_branch is 'main' )
def download_output_repo():
    print('download_output_repo -> pwd', __cur_dir)
    dest = path_join(__cur_dir, 'output')
    print('dest', dest)

    # clear temp lib dir
    if os.path.exists(dest):
        print('clear output at', dest)
        delete_dir(dest)

    # clone lib
    print('create output at', dest)
    os.makedirs(dest)
    run_cmd(f'git clone {SDK_LIB_REPO} .', dest)

    return dest
    pass


# download the source proj 'unity-gurusdk-dev'
# and the output proj 'unity-gurusdk-library'
def download_all_repos(dev_branch: str):
    # download source and output
    source = download_source_repo(dev_branch)
    output = download_output_repo()
    output_success('download complete')
    pass


# collect call upm files from dev_project，
# and collect them into ‘dev_project/packages’ path
# all ump repos from GitHub will be cloned
def collect_upm_dependencies_and_version(source_repo_path: str, ):

    sdk_upm_home = path_join(source_repo_path, 'packages')
    unity_proj_path = path_join(source_repo_path, UNITY_DEV_PROJECT)
    packages_path = path_join(unity_proj_path, UNITY_PACKAGES_ROOT)
    # manifest_file = join_path(packages_path, "manifest.json")
    lock_file = path_join(packages_path, UNITY_PACKAGES_LOCK_JSON)
    config_file = path_join(packages_path, SDK_CONFIG_JSON)

    if not os.path.exists(config_file):
        print('can not found <sdk-config>', config_file)
        return None

    if not os.path.exists(lock_file):
        print('can not found <packages-lock>', lock_file)
        return None

    f = read_file(config_file)
    sdk_config = json.loads(f)
    version = sdk_config['version']
    run_cmd(f"cp {config_file} {path_join(sdk_upm_home, SDK_CONFIG_JSON)}")

    # parse packages-lock.json
    f = read_file(lock_file)
    lock_data = json.loads(f)
    additions = []
    for pkg_id in lock_data['dependencies']:

        item = lock_data['dependencies'][pkg_id]

        if item is None:
            continue

        if item['source'] == 'git':
            # git upm
            # hash = item['hash']
            git_url = item['version']
            to_path = path_join(sdk_upm_home, pkg_id)

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
            additions.append(to_path)
            pass
        pass

    return version, additions
    pass


# update current version info into version_list file
def update_version_list(to_path: str, out_path: str):

    cfg_path = path_join(to_path, SDK_CONFIG_JSON)
    if not os.path.exists(cfg_path):
        print('file not found:', cfg_path)
        exit(-1)

    sdk_config = json.loads(read_file(cfg_path))
    if sdk_config is None:
        print('parse sdk-config with wrong value')
        exit(-10)

    sdk_version = sdk_config['version']
    desc = sdk_config['desc']

    file_path = path_join(out_path, VERSION_LIST)

    # try to load or create version_list.json
    if os.path.exists(file_path):
        t = read_file(file_path)
        version_list = json.loads(t)
    else:
        version_list = {'latest': '', 'versions': {}}

    version_list['latest'] = sdk_version
    version_list['versions'][sdk_version] = {}
    version_list['versions'][sdk_version]['ts'] = int(datetime.datetime.today().timestamp())

    if len(desc) > 0:
        version_list['versions'][sdk_version]['desc'] = desc

    write_file(file_path, json.dumps(version_list))
    pass


# init all the args from input
def init_args():
    parser = argparse.ArgumentParser(description='guru-sdk cli tool')
    parser.add_argument('action', type=str, help='sync, install, publish, quick_publish, delete_version, debug_source, test')
    parser.add_argument('--version', type=str, help='version for publish')
    parser.add_argument('--branch', type=str, help='branch for pulling all library repo')
    parser.add_argument('--source_path', type=str, help='local source dev project path')
    parser.add_argument('--proj', type=str, help='unity project path')
    parser.add_argument('--pkgs', type=str, help='package list which will be installed')

    return parser.parse_args()


# Entry of the cli.
if __name__ == '__main__':
    print(f'========== Welcome to GuruSdk CLI [{VERSION}] ==========')
    args = init_args()
    __cur_dir = os.getcwd()
    print('OS', os.name)
    print('Action:', args.action)
    print('PWD', __cur_dir)
    print('SDK_HOME', get_sdk_home())

    action: str = args.action
    version: str = args.version
    branch: str = args.branch
    source_path: str = args.source_path
    pkgs: str = args.pkgs
    proj: str = args.proj

    # only sync version on client
    if action == 'sync':
        # sync the latest version of guru_sdk
        sync_sdk()
        pass
    # sync and then install selected version for client
    if action == 'install':
        if not os.path.exists(proj):
            print(f'Can not found unity project at\n{proj}')
            exit(ERROR_UNITY_PROJECT_NOT_FOUND)
            pass

        if len(version) == 0:
            print('wrong version format')
            exit(ERROR_WRONG_VERSION)
            pass

        sync_and_install_sdk(proj, version)

    # publish version by jenkins
    elif action == 'publish':
        # publish sdk with special version
        if len(branch) == 0:
            print('empty branch name')
            branch = 'publish'
        else:
            publish_sdk_by_cli(branch)
        pass

    # publish version directly from unity
    elif action == 'quick_publish':
        # publish sdk by unity project inside cmd
        if len(source_path) == 0:
            print('empty source_path, make sure you were on the right path!')
            exit(ERROR_WRONG_SOURCE_PATH)
        else:
            publish_sdk_by_unity(source_path)
        pass

    # only download repos for debug
    elif action == 'debug_source':
        if branch is None or len(branch) == 0:
            print('empty branch name')
            branch = 'main'
        else:
            download_all_repos(branch)

    elif action == 'test':
        cp = os.getcwd()
        print('current path', cp)
        pass

    # print('get ts', int(datetime.datetime.today().timestamp()))

    pass
