import os
import subprocess
import sys
from configparser import ConfigParser


db_password = input('Enter the password for database: ')
db_name = input('Enter the desired name for your Chat database: ')

if os.name == 'posix':

    pms = {
        'pacman': 'pacman -S',
        'apt': 'apt',
        'yum': 'yum install',
        'rpm': 'rpm -i',
        'dnf': 'dnf install',
    }
    os.environ['DB_PASSWORD'] = db_password
    os.environ['DB_NAME'] = db_name

    if sys.platform == 'darwin':
        subprocess.run(['bash', 'install_macos.sh'], cwd='scripts')
    else:
        print('Choose your package manager: ')
        for i, pm in enumerate(pms.keys()):
            print(f"{i+1}. {pm}")

        choice = int(input('Enter the number of your package manager (0 - other PM): '))
        if choice == 0:
            print('Please edit "install_linux.sh" script to fit your needs.')
            input('Press Enter key to leave...')
            sys.exit(0)

        pm_choice = list(pms.keys())[choice-1]

        os.environ['PM'] = pms[pm_choice]

        subprocess.run(['bash', 'install_linux.sh'], cwd='scripts')
else:
    subprocess.run(['install_win.bat', db_password, db_name], cwd='scripts')

config = ConfigParser()
config.add_section('Database')
config.set('Database', 'DB_PASSWORD', db_password)
config.set('Database', 'DB_NAME', db_name)    

with open('server.ini', 'w') as cfg:
    config.write(cfg)