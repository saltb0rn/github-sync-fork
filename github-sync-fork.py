#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# github-fork-sync.py


import argparse
import subprocess
import sys
import os
from urllib.parse import urlparse

import requests

git_status_cmd = None
current_repo_cmd = None
add_remote_cmd = None
check_remote_cmd = None
checkout_master_cmd = None
fetch_remote_cmd = None
merge_upstream_cmd = None
push_repo_cmd = None


def sync():

    global git_status_cmd
    global current_repo_cmd
    global add_remote_cmd
    global check_remote_cmd
    global checkout_master_cmd
    global fetch_remote_cmd
    global merge_upstream_cmd
    global push_repo_cmd

    parser = argparse.ArgumentParser(
        description="Sync fork of a repo on GitHub")
    parser.add_argument('-r', '--repo',
                        default=".", help="the local repo on you machine")
    args = parser.parse_args()

    local_repo_path = os.path.expanduser(args.repo)

    git_status_cmd = ["git", "-C", local_repo_path, "status"]
    current_repo_cmd = [
        'git', "-C", local_repo_path, 'config', '--get', 'remote.origin.url']
    add_remote_cmd = [
        'git', "-C", local_repo_path, 'remote', 'add', 'upstream']
    check_remote_cmd = [
        "git", "-C", local_repo_path, "remote", "-v"]
    checkout_master_cmd = [
        'git', "-C", local_repo_path, 'checkout', 'master']
    fetch_remote_cmd = [
        'git', "-C", local_repo_path, 'fetch', 'upstream']
    merge_upstream_cmd = [
        'git', "-C", local_repo_path, 'merge', 'upstream/master']
    push_repo_cmd = [
        'git', "-C", local_repo_path, 'push', 'origin', 'master']

    subprocess.check_call(git_status_cmd, stdout=subprocess.DEVNULL)

    print("Checking parent repo ... ")

    repo_url = subprocess.check_output(
        current_repo_cmd).decode().split(".git\n")[0]
    request = "https://api.github.com/repos{}".format(
        urlparse(repo_url).path)
    response = requests.get(request)
    parent_url = response.json()['parent']['git_url']

    print("The upstream is {}".format(parent_url))
    if parent_url in subprocess.check_output(check_remote_cmd).decode():
        pass
    else:
        add_remote_cmd.append(parent_url)
        subprocess.check_call(add_remote_cmd)

    print("Fetching upstream ...")
    subprocess.check_call(fetch_remote_cmd)
    subprocess.check_output(checkout_master_cmd)

    print("Merging upstream and master")
    subprocess.check_call(merge_upstream_cmd)

    print("Pushing to your fork repo")
    subprocess.check_output(push_repo_cmd)


if __name__ == "__main__":
    try:
        sync()
    except Exception as e:
        e_type, e_value, _ = sys.exc_info()
        if (e_type is subprocess.CalledProcessError and
            hasattr(e, "cmd") and
            e.cmd == git_status_cmd):
            print("This is not a repo")
        elif (e_type is subprocess.CalledProcessError and
              hasattr(e, "cmd") and
              e.cmd == current_repo_cmd):
            print("Couldn't get the user and repo names from the Git config.")
        elif e_type is KeyError:
            print("It seems your repo is not a fork")
        elif (e_type is subprocess.CalledProcessError and
              (e.cmd in [merge_upstream_cmd, checkout_master_cmd])):
            print("Can not merge. Reason: ", e.output.decode())
        else:
            pass
    else:
        print('Everything done')
