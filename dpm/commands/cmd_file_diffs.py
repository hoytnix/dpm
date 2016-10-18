import os
import shutil
import json
import hashlib

import click

from dpm.tasks.fs import local_directory

package_directory = local_directory(path='file_diffs')


def file_checksum(fp):
    try:
        with open(fp, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:    # File does not exist yet.
        return ""


@click.group()
def cli():
    """Utility for collecting files which have changed. Useful for configurations.

    Packages-file is in ~/.local/share/dpm/file_diffs/packages.json
    """
    pass


@cli.command()
def collect():
    """Collect files which have changed."""

    # Get database.
    with open(local_directory(path='file_diffs/packages.json'), 'r') as f:
        store = json.load(f)

    # UI.
    print('Checking files for differences...\n')

    # Iterate database.
    for package_name in store:
        # Package variables.
        package_dir = os.path.join(package_directory, package_name)
        package = store[package_name]

        # Recursive (lazy) package searching.
        if type(package) == str:
            package = os.path.expanduser(package)
            for dirpath, dirnames, filenames in os.walk(package):
                for filename in filenames:
                    sub_package_dir = package_dir + dirpath.replace(package, '')
                    if not os.path.exists(sub_package_dir):
                        os.makedirs(sub_package_dir)

                    fp_local = os.path.join(dirpath, filename)
                    fp_remote = os.path.join(sub_package_dir, filename)

                    cs_local = file_checksum(fp=fp_local)
                    cs_remote = file_checksum(fp=fp_remote)

                    if cs_remote != cs_local:
                        print('Found: {}/{}'.format(package_name, filename))
                        shutil.copyfile(src=fp_local, dst=fp_remote)

        # Manual package searching.
        if type(package) == list:
            for fp in package:
                fn_local = fp['local']
                fn_remote = fp['remote']

                fp_local = os.path.expanduser(fn_local)
                fp_remote = os.path.join(package_dir, fn_remote)

                cs_local = file_checksum(fp=fp_local)
                cs_remote = file_checksum(fp=fp_remote)

                if cs_remote != cs_local:
                    print('Found: {}/{}'.format(package_name, fn_remote))

                    remote_dir_path = '/'.join(fp_remote.split('/')[:-1])
                    if not os.path.exists(remote_dir_path):
                        os.makedirs(remote_dir_path)
                    shutil.copyfile(src=fp_local, dst=fp_remote)
