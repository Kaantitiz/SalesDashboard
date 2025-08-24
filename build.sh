#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Direkt veritabanı oluşturma
python direct_db.py
