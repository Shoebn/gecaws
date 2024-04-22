SCRIPT_NAME=scheduler_linux
LOG_DIR=/GeC/gecftp/logs
GIT_ROOT_DIR=/GeC/gecsamba/gecscraping/live_scripts
TODAY=$(date +\%d-\%m-\%Y)
nohup python3 -u "$SCRIPT_NAME.py" >> $LOG_DIR/"$SCRIPT_NAME"-"$TODAY".log 2>&1 &
