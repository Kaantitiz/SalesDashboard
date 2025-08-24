#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Veritabanı başlatma ve kullanıcı oluşturma
python init_db.py
