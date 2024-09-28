#! /bin/bash

python -m venv env
source env/bin/activate
pip install -r requirements.txt

python generate_ssl_tls.py
python setup.py

