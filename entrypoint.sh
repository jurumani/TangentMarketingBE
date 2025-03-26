#!/bin/bash

LOGFILE="./logfile.log"

echo "Starting migrations..." | tee -a $LOGFILE
python manage.py makemigrations 2>&1 | tee -a $LOGFILE

echo "Applying migrations..." | tee -a $LOGFILE
python manage.py migrate 2>&1 | tee -a $LOGFILE

echo "Starting server..." | tee -a $LOGFILE
python manage.py runserver 0.0.0.0:8000 2>&1 | tee -a $LOGFILE