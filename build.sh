#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Basit kullanıcı oluşturma scripti çalıştır
python create_user.py
