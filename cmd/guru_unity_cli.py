#! /usr/bin/python3
# coding=utf-8

"""
GuruSDK CLI Tool
A command line interface for managing GuruSDK installation and publishing
"""

import argparse
import os
import shutil
import json
import datetime
import requests
from os.path import expanduser

# Define constants
VERSION = '0.5.0'
# DESC = 'Fix bug: publish sdk with empty folders. bug: install sdk on windows get Error in batch'
DESC = 'Restructured the entire UPM Repos from scattered repos to one big repo. (v2) 2024-12-24'

# Define paths
SDK_CONFIG_JSON = 'sdk-config.json'  # SDK 开发者定义的 upm 包的配置关系，包含所有包体的可选以及从属关系, [需要配置在 DEV 项目]
SDK_HOME_PATH = '.guru/unity/guru-sdk'  # 用户设备上缓存 SDK 各个版本的路径
SDK_TEMP_PATH = '.guru/unity/temp'  # 用户设备上临时缓存路径
SDK_LIB_REPO = 'git@github.com:castbox/unity-gurusdk-library.git'  # 线上发布的 SDK 静态库的 repo
SDK_DEV_REPO = 'git@github.com:castbox/unity-gurusdk-dev.git'  # SDK 开发者所使用的开发 Repo
SDK_LIB_V2 = 'com.guru.unity.sdk.v2'  # SDK upm 整体合并后的 lib 版本（V2）
UPM_PREFIX = '.upm.'  # 在用户的项目中 Packages 的路径前缀
UNITY_MANIFEST_JSON = 'manifest.json'  # unity 项目自身的 UPM 包清单文件
UNITY_PACKAGES_LOCK_JSON = 'packages-lock.json'  # unity 项目自身的 UPM 包清单文件
UNITY_PACKAGES_ROOT = 'Packages'  # unity 项目自身的 UPM 包清单文件
UNITY_DEV_PROJECT = 'GuruSDKDev'  # unity 开发项目中 Unity 工程路径的二级目录
VERSION_LIST = 'version_list.json'  # SDK 版本描述文件
VERSION_LIST_URL = 'https://raw.githubusercontent.com/castbox/unity-gurusdk-library/refs/heads/main/version_list.json'
LOG_TXT = 'log.txt'

ERROR_UNITY_PROJECT_NOT_FOUND = 100
ERROR_WRONG_VERSION = 101
ERROR_WRONG_SOURCE_PATH = 102
ERROR_SDK_CONFIG_NOT_FOUND = 103
ERROR_SDK_CONFIG_LOAD_ERROR = 104
ERROR_PATH_NOT_FOUND = 405
ERROR_WRONG_ARGS_FORMAT = 501

# global cmd_root var
CURRENT_PATH = os.getcwd()


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
    return to_safe_path(f'{get_user_home()}/{SDK_HOME_PATH}')


# check is running on windows sys
def is_windows_platform():
    return os.name == 'nt'


def is_empty_str(txt: str):
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


def clear_log():
    path = f'{CURRENT_PATH}/{LOG_TXT}'
    if os.path.exists(path):
        os.remove(path)


def save_log_txt(txt: str):
    path = f'{CURRENT_PATH}/{LOG_TXT}'
    write_file(path, txt)


def log_success(content: str):
    if is_empty_str(content):
        content = '...'

    txt = f'success: {content}'
    save_log_txt(txt)


def log_failed(content: str):
    if is_empty_str(content):
        content = '...'

    txt = f'failed: {content}'
    save_log_txt(txt)


def get_timestamp():
    return int(datetime.datetime.utcnow().timestamp())


# ---------------------- Install ----------------------
# install from unity project
def install_by_unit_proj(unity_proj: str):
    sdk_data = path_join(unity_proj, f'ProjectSettings/guru-sdk-installer.json')
    if not os.path.exists(sdk_data):
        exit(ERROR_PATH_NOT_FOUND)

    doc = json.loads(read_file(sdk_data))
    version = doc['install_version']
    sync_and_install_sdk(unity_proj, version)


# sync and install sdk from local cache
def sync_and_install_sdk(unity_proj: str, version: str):
    clear_log()

    version_home = path_join(get_sdk_home(), VERSION_LIST)

    if not os.path.exists(version_home):
        # version not exists
        # 1st time try to sync latest lib repo
        sync_sdk(False)
        # 2nd if version_home still not exists
        if not os.path.exists(version_home):
            print(f'Version not found {version}, check version_list first!')
            log_failed(f'version not exists: {version}')
            exit(ERROR_PATH_NOT_FOUND)
    else:
        # check version should update
        local_version_list = json.loads(read_file(version_home))
        need_update = True
        if version in local_version_list['versions']:
            need_update = should_update_sdk(version, str(local_version_list['versions'][version]['ts']))

        if need_update:
            sync_sdk(False)

    install_sdk_to_project(unity_proj, version)
    pass


def should_update_sdk(version: str, ts: str):
    if is_empty_str(version) or is_empty_str(ts):
        return True

    # check online version list
    resp = requests.get(VERSION_LIST_URL)
    if resp.status_code == 200:
        doc = resp.json()
        for v in doc['versions']:
            if v == version:
                online_ts = str(doc['versions'][v]['ts'])
                if online_ts == ts:
                    print(f'Version [{version}] :: local:[{ts}] not match online:[{online_ts}], need to update sdk')
                    return False
        pass
    return True


# download latest sdk
def sync_sdk(show_log: bool = True):
    sdk_home = get_sdk_home()

    # only support for quick clone, so every time it will remove all files, then clone it again
    if os.path.exists(sdk_home):
        # remove old files
        delete_dir(sdk_home)
        pass
    os.makedirs(sdk_home)

    print(f'Clone sdk into {sdk_home}')
    run_cmd(f'git clone --depth 1 {SDK_LIB_REPO} .', sdk_home)

    if show_log:
        log_success('sync complete')
    pass


# sync latest sdk repo to the path '~/.guru/unity/guru-sdk'
def install_sdk_to_project(unity_proj_path: str, version: str):
    sdk_home = get_sdk_home()
    version_home = path_join(sdk_home, version)
    upm_root = path_join(unity_proj_path, UNITY_PACKAGES_ROOT)
    manifest_path = path_join(unity_proj_path, f'{UNITY_PACKAGES_ROOT}/{UNITY_MANIFEST_JSON}')
    sdk_config = path_join(version_home, SDK_CONFIG_JSON)

    if not os.path.exists(sdk_config):
        print(f'sdk-config not found:: \n{sdk_config}')
        exit(ERROR_SDK_CONFIG_NOT_FOUND)
        pass

    # clean old sdk files
    clean_old_soft_links(upm_root)

    manifest_json = load_unity_manifest_json(manifest_path)
    if manifest_json is None:
        return

    # install all packages from sdk-config
    with open(sdk_config, 'r', encoding='utf-8') as f:
        txt = f.read()
        # print(txt)
        cfg = json.loads(txt)

        if cfg is None or cfg['packages'] is None:
            print('json parse error with', sdk_config, 'plz fix the errors')
            return

        for p in cfg['packages']:
            in_path = path_join(version_home, p)
            if not os.path.exists(in_path):
                print(f'package [{p}] not found, skip install...')
                continue

            print(f'Add package at path: {in_path}')
            make_softlink(in_path, p, upm_root)

            # record deps
            manifest_json['dependencies'][p] = f'file:{UPM_PREFIX}{p}'
            pass
        # save the manifest file
        save_unity_manifest_json(manifest_path, manifest_json)
        pass
    pass

    # add .gitignore file
    make_git_ignore(unity_proj_path)

    log_success('install complete')


def clean_old_soft_links(upm_root: str):
    if not os.path.exists(upm_root):
        print(f'Path not found: {upm_root}')
        exit(ERROR_PATH_NOT_FOUND)

    dirs = os.listdir()
    for d in dirs:
        if d.startswith(UPM_PREFIX):
            # clean the old softlink
            delete_dir(path_join(upm_root, d))
    pass


# create softlink with os cmd
def make_softlink(source_path: str, link_name: str, dest_dir: str):
    if is_empty_str(source_path):
        print(f'wrong source_path: [{source_path}]')
        exit(ERROR_WRONG_ARGS_FORMAT)

    link_path = path_join(dest_dir, f'{UPM_PREFIX}{link_name}')

    # delete old link
    if os.path.exists(link_path):
        os.remove(link_path)

    if is_windows_platform():
        # run_cmd(f'mklink /D {dest_dir}\\{link_name} {source_path}')
        os.symlink(source_path, link_path)
        pass
    else:
        cmd = f'ln -s {source_path} {link_path}'
        print(f'make softlink >> [{source_path}] -> [{link_path}]')
        run_cmd(cmd)
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
        json_str = json.dumps(data, indent=2)
        f.write(json_str)
        f.close()
    pass


def make_git_ignore(unity_project: str):
    file = path_join(unity_project, '.gitignore')
    comments = '# Guru UPM'
    old_line = f'{comments}\nPackages/{UPM_PREFIX}*'
    keep_manifest = '!Packages/manifest.json'
    keep_package_lock = '!Packages/packages-lock.json'
    keep_sdk_config = '!Packages/sdk-config.json'
    ignore_line= 'Packages/*'
    content = f'{comments}\n{keep_manifest}\n{keep_package_lock}\n{keep_sdk_config}\n{ignore_line}\n\n'

    if os.path.exists(file):
        txt = read_file(file)

        need_write = False
        if comments in txt:
            # 删除老的
            if old_line in txt:
                txt = txt.replace(old_line, '')
                need_write = True
        else:
            need_write = True

        if not need_write:
            return

        # 写入新的忽略
        txt = txt + f'\n{content}'
        write_file(file, txt)

    else:
        # add ignore line in
        write_file(file, content)




# ---------------------- PUBLISH ----------------------
# publish the new version
def publish_and_push(source: str, output: str):
    # clone all remote upms
    _version, sdk_config = build_version_packages_and_files(source, output)

    # update version list
    update_version_list(sdk_config, output)

    push_msg = f'Make version {_version} on  {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}  by push'

    # commit to the publishing repo
    run_cmd(f'git add .', output)
    run_cmd(f'git commit -m \"{push_msg}\"', output)
    run_cmd(f'git push', output)

    print('===== Publish is done! ======')

    # if clean_mode == 1:
    #     delete_dir(source)
    #     delete_dir(output)
    # elif clean_mode == 2:
    #     delete_dir(output)
    # pass


# publish sdk vai cil or jenkins
def publish_sdk_by_cli(publish_branch: str):
    # clean old dirs
    td = path_join(CURRENT_PATH, 'source')
    delete_dir(td)
    td = path_join(CURRENT_PATH, 'output')
    delete_dir(td)
    # download all repos
    source = download_source_repo(publish_branch)
    output = download_output_repo()
    publish_and_push(source, output)
    pass


# publish sdk from local cmd from unity project
def publish_from_unity_project(unity_project: str):
    # print('--- unity_project:', unity_project)
    source = os.path.dirname(unity_project)
    print('--- source:', source)
    op = path_join(get_user_home(), SDK_TEMP_PATH)
    output = download_output_repo(op)
    print('--- output:', output)
    publish_and_push(source, output)
    delete_dir(output)
    pass


# download unity-gurusdk-dev repo to dest path ( the default pull_branch is 'main' )
def download_source_repo(pull_branch: str = ''):
    dest = path_join(CURRENT_PATH, 'source')

    # clear source from last pull
    if os.path.exists(dest):
        print('clear source path')
        delete_dir(dest)

    if len(pull_branch) == 0:
        pull_branch = 'main'

    print(f'--- pull code form {SDK_DEV_REPO} with branch: {pull_branch}')
    print(f'--- create source at {dest}')
    os.makedirs(dest)
    run_cmd(f'git clone -b {pull_branch} --depth=1 {SDK_DEV_REPO} .', dest)
    run_cmd(f'git submodule update --init --recursive', dest)

    return dest
    pass


# download unity-gurusdk-library repo to dest path ( the default pull_branch is 'main' )
def download_output_repo(root: str = ''):
    if is_empty_str(root):
        root = CURRENT_PATH
        print(f'--- empty input root value, set to current dir: {root}')

    print('download_output_repo -> root:', root)
    dest = path_join(root, 'output')
    print('dest', dest)

    # clear temp lib dir
    if os.path.exists(dest):
        print('clear output path')
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
    log_success('download complete')
    return source, output
    pass


# collect call upm files from dev_project，
# and collect them into ‘dev_project/packages’ path
# all ump repos from GitHub will be cloned
def build_version_packages_and_files(source: str, output: str):
    packages = path_join(source, 'packages')
    unity_proj_path = path_join(source, UNITY_DEV_PROJECT)
    packages_path = path_join(unity_proj_path, UNITY_PACKAGES_ROOT)
    # package_cache = path_join(unity_proj_path, 'Library/PackageCache')
    # manifest_file = join_path(packages_path, "manifest.json")
    lock_file = path_join(packages_path, UNITY_PACKAGES_LOCK_JSON)
    config_file = path_join(packages_path, SDK_CONFIG_JSON)

    # sdk-config.json must exist
    if not os.path.exists(config_file):
        print('can not found <sdk-config>', config_file)
        return None
    # packages-lock.json must exist
    if not os.path.exists(lock_file):
        print('can not found <packages-lock>', lock_file)
        return None
    # load skd-config.json
    sdk_config = json.loads(read_file(config_file))
    if sdk_config is None:
        print('load config error <sdk-config>', config_file)
        exit(ERROR_SDK_CONFIG_LOAD_ERROR)

    sdk_config['ts'] = f'{get_timestamp()}' # write ts on publish date
    sdk_version = sdk_config['version']

    # pull all submodules
    sc = f'git submodule update --init --recursive'
    run_cmd(sc, source)

    # clean and rebuild version folder
    dest = path_join(output, sdk_version)
    if os.path.exists(dest):
        delete_dir(dest)

    ensure_dir(dest)

    # copy submodules into version dir
    run_cmd(f"cp {config_file} {path_join(dest, SDK_CONFIG_JSON)}")

    # # 1. copy all submodules in packages to dest
    # for item in os.listdir(submodules):
    #     dd = os.path.join(submodules, item)
    #     if os.path.isdir(dd):
    #         shutil.copytree(dd, path_join(dest, item))

    # 1.1 copy all sub folder in lib v2 to dest
    lib_v2 = path_join(packages, SDK_LIB_V2)
    if not os.path.exists(lib_v2):
        print(f'path not found: {lib_v2} !')
        exit(ERROR_PATH_NOT_FOUND)
        pass

    for item in os.listdir(lib_v2):
        from_path = os.path.join(lib_v2, item)
        if os.path.isdir(from_path):
            if item.startswith('.'):
                continue

            to_path = path_join(dest, item)
            shutil.copytree(from_path, to_path)

    # 2. clone all git upm from packages-lock.json to dest
    f = read_file(lock_file)
    lock_data = json.loads(f)
    # additions = []
    for pkg_id in lock_data['dependencies']:

        item = lock_data['dependencies'][pkg_id]

        if item is None:
            continue

        if item['source'] == 'git':
            # git upm
            git_hash = item['hash']
            git_url = item['version']
            if '#' in git_url:
                git_url = git_url.split('#')[0]

            to_path = path_join(dest, pkg_id)

            if os.path.exists(to_path):
                delete_dir(to_path)

            os.mkdir(to_path)

            print(f'clone {pkg_id}: {git_url} -> {to_path}')

            sc = f'git clone --depth 1 {git_url} .'
            run_cmd(sc, to_path)
            sc = f'git checkout {git_hash}'
            run_cmd(sc, to_path)

            # delete .git folder in cloned folder
            _git = path_join(to_path, '.git')
            delete_dir(_git)

            # additions.append(to_path)
            pass
        pass

    return sdk_version, sdk_config
    pass


# update current version info into version_list file
def update_version_list(sdk_config: dict, out_path: str):
    if sdk_config is None:
        print('parse sdk-config with wrong value')
        exit(ERROR_SDK_CONFIG_NOT_FOUND)

    sdk_version = sdk_config['version']
    desc = sdk_config['desc']

    file_path = path_join(out_path, VERSION_LIST)

    # try to load or create version_list.json
    if os.path.exists(file_path):
        t = read_file(file_path)
        version_list = json.loads(t)
    else:
        version_list = {'latest': '', 'versions': {}}

    if is_empty_str(desc):
        desc = 'not set yet'

    version_list['latest'] = sdk_version
    version_list['versions'][sdk_version] = {}
    version_list['versions'][sdk_version]['ts'] = get_timestamp()
    version_list['versions'][sdk_version]['desc'] = desc

    write_file(file_path, json.dumps(version_list))
    pass


def debug_repos(branch: str):
    source, output = download_all_repos(branch)
    build_version_packages_and_files(source, output)


def debug_test_func():
    cp = CURRENT_PATH
    print('current path', cp)

    time_str = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    print('time', time_str)

    ts = int(datetime.datetime.utcnow().timestamp())
    print('ts', ts)

    # p = '/Users/huyfuei/Workspace/Castbox/SDK/GuruSDK/unity-gurusdk-dev/GuruSDKDev/'
    # root = os.path.dirname(p)
    # print('root', root)
    # publish_from_unity_project(p)

    pass


# ======================================================================================================================
# init all the args from input
def init_args():
    parser = argparse.ArgumentParser(description='guru-sdk cli tool')
    parser.add_argument('action', type=str,help='sync, install, unity_install, publish, quick_publish, delete_version, debug_source, test')
    parser.add_argument('--version', type=str, help='version for publish')
    parser.add_argument('-b','--branch', type=str, help='branch for pulling all library repo')
    parser.add_argument('-p','--proj', type=str, help='unity project path')
    parser.add_argument('--pkgs', type=str, help='package list which will be installed')

    return parser.parse_args()


# main function for cli enter point
def main():
    print(f'========== Welcome to GuruSDK CLI [{VERSION}] ==========')
    print(f'UPDATE:{DESC}\n')

    args = init_args()
    print('OS:', os.name)
    print('Action:', args.action)
    print('CMD_ROOT:', CURRENT_PATH)
    print('SDK_HOME:', get_sdk_home())

    action: str = args.action
    version: str = args.version
    branch: str = args.branch
    pkgs: str = args.pkgs
    proj: str = args.proj

    # only sync version on client
    if action == 'sync':
        clear_log()
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

    # install from unity project
    if action == 'unity_install':
        if not os.path.exists(proj):
            print(f'Can not found unity project at\n{proj}')
            exit(ERROR_UNITY_PROJECT_NOT_FOUND)

        install_by_unit_proj(proj)
        pass

    # 链接 SDK
    if action == 'link':

        pass

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
        if is_empty_str(proj):
            print('empty source_path, make sure you were on the right path!')
            exit(ERROR_WRONG_SOURCE_PATH)
        else:
            if is_windows_platform():
                if proj[-1] == '\\':
                    proj = proj[:-2]  # delete end '\\' char
            else:
                if proj[-1] == '/':
                    proj = proj[:-2]  # delete end '/' char
            publish_from_unity_project(proj)
        pass

    # only download repos for debug
    elif action == 'debug_source':
        if branch is None or len(branch) == 0:
            print('empty branch name')
            branch = 'main'
        else:
            debug_repos(branch)

    # test function
    elif action == 'test':
        debug_test_func()
        pass

    # print('get ts', int(datetime.datetime.today().timestamp()))
    pass


# Entry of the cli.
if __name__ == '__main__':
    main()
