import getpass
import platform
import socket
from pathlib import Path

from agio.core.entities.profile import AProfile


def collect_user_info():
    profile = AProfile.current()
    user_info = {
        'id': profile.id,
        'name': getpass.getuser(),
        'email': profile.email,
        'first_name': profile.first_name,
        'last_name': profile.last_name,
        'language': profile.language,
        'home_path': Path.home().as_posix()
    }
    return user_info


def collect_host_info():
    # TODO: use agio.tools.platform_info.get_platform_variables
    host_data = {
        'hostname': socket.gethostname(),
        'system': platform.system().lower(),
        'os_name': '',
        'os_version': '',
        'platform': platform.platform()
    }
    if host_data['system'] == 'linux':
        info = platform.freedesktop_os_release()
        host_data['os_name'] = info["NAME"]
        host_data['os_version'] = info["VERSION_ID"]
    elif host_data['system'] == 'darwin':
        raise NotImplementedError
        # info = platform.mac_ver()
    else:
        parts = platform.version().rsplit('.')
        vers = parts[0]
        build = parts[-1]
        if vers== '10' and int(build) >= 22000:
            vers = '11'
        host_data['os_version'] = vers
        host_data['os_name'] = platform.uname().system
    return host_data