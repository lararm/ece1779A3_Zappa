#!c:\users\larissa\documents\uoft\intro_cloud_computing\a3zappa\flask_zappa\flask_zappa\venv\scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'kappa==0.6.0','console_scripts','kappa'
__requires__ = 'kappa==0.6.0'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('kappa==0.6.0', 'console_scripts', 'kappa')()
    )
