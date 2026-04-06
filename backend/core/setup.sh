#!/bin/bash
python -m venv venv
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

python manage.py migrate
python manage.py runserver