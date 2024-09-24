import os
import subprocess
import sys
from configparser import ConfigParser
from io import StringIO

from encryption import encrypt_aes


db_password = input('Enter the password for database: ')
while True:
    db_name = input('Enter the desired name for your Chat database: ').lower()
    if not db_name.isalpha():
        print("Only lowercase latin chars accepted.")
        continue
    break

encryption_key = input("""
Enter encryption key for your config.
YOU'LL NEED TO ENTER IT EACH TIME YOU RUN YOUR SERVER!!!
(16-characters max, overflow will be cut): 
""").rjust(16, "0")[:16]

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

        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("Virtual environment:", sys.prefix)
        else:
            print("No virtual environment detected.")
        subprocess.run(['bash', 'install_linux.sh'], cwd='scripts')
else:
    subprocess.run(['install_win.bat', db_password, db_name], cwd='scripts')


config = ConfigParser()
config.add_section('Database')
config.set('Database', 'DB_PASSWORD', db_password)
config.set('Database', 'DB_NAME', db_name)    

output = StringIO()
config.write(output)
conf = output.getvalue()

encrypted_conf, _ = encrypt_aes(conf.encode(), key=encryption_key.encode())

with open('server.conf.enc', 'wb') as cfg:
    cfg.write(encrypted_conf)

