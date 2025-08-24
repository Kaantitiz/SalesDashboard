#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# PostgreSQL migration çalıştır
python migrations.py
