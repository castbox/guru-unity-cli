#!/usr/bin/env python3

import argparse
import os
import shutil
import json
from os.path import expanduser

# CONSTS
VERSION = '0.1.0'
SDK_HOME = '.guru/unity/guru_sdk'
SDK_LIB_REPO = 'https://github.com/castbox/unity-gurusdk-library.git'
SDK_DEV_REPO = 'git@github.com:castbox/unity-gurusdk-dev.git'


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


# download latest sdk
def sync_guru_sdk():
    user_home = expanduser("~")
    sdk_home = os.path.join(user_home, SDK_HOME)

    if os.path.exists(sdk_home):
        # remove old files
        delete_dir(sdk_home)
        pass

    os.mkdir(sdk_home)
    run_cmd(f'git clone --depth 1 {SDK_LIB_REPO} .', sdk_home)
    pass


# publish the new version
def publish_guru_sdk(version: str, branch: str):
    pwd = os.getcwd()
    print('cmd path:', pwd)

    source = os.path.join(pwd, 'source')
    output = os.path.join(pwd, 'output')
    pkg_path = os.path.join(source, 'packages')



    if os.path.exists(source):
        delete_dir(source)

    if os.path.exists(output):
        delete_dir(output)

    if len(branch) == 0:
        branch = 'main'

    # clone dev
    os.mkdir(source)
    run_cmd(f'git clone -b {branch} {SDK_DEV_REPO} .', source)
    run_cmd(f'git submodule update --init --recursive', source)

    # clone lib
    os.mkdir(output)
    run_cmd(f'git clone {SDK_LIB_REPO} .', output)

    # clone all remote upms
    collect_upm_pkgs(source)

    to_path = os.path.join(output, version)

    if os.path.exists(to_path):
        delete_dir(to_path)

    # make version dir
    shutil.copytree(pkg_path, to_path)


    # todo 解析和生成对应的配置文件， 并且下载所有对应的第三方 upm 至 to_path


    pass


# collect call path info from dev project
def collect_upm_pkgs(root_path: str):
    info = {}

    upm_path = os.path.join(root_path, 'packages')
    unity_proj_path = os.path.join(root_path, 'GuruSDKDev')
    packages_path = os.path.join(unity_proj_path, 'Packages')
    # manifest_file = os.path.join(packages_path, "manifest.json")
    lock_file = os.path.join(packages_path, "packages-lock.json")
    config_file = os.path.join(packages_path, "sdk-config.json")

    if not os.path.exists(config_file):
        print('can not found <sdk-config>', config_file)
        return None

    if not os.path.exists(lock_file):
        print('can not found <packages-lock>', lock_file)
        return None

    info = {}

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
                to_path = os.path.join(upm_path, pkg_id)

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

        run_cmd(f"cp {config_file} {os.path.join(upm_path,'sdk_config.json')}")

    pass


def init_args():
    parser = argparse.ArgumentParser(description='gurusdk cli tool')
    parser.add_argument('action', type=str, help='sync,init,publish')
    parser.add_argument('--platform', type=str, help='flutter or unity')

    return parser.parse_args()


# Entry of the cli.
if __name__ == '__main__':
    print(f'========== Welcome to GuruSdk CLI [{VERSION}] ==========')
    args = init_args()

    print('Action:', args.action)

    if args.action == 'sync':
        # sync the latest version of guru_sdk
        sync_guru_sdk()
    elif args.action == 'publish':
        # publish sdk with special version
        publish_guru_sdk('1.1.7', 'hotfix/V1.1.7')

    pass