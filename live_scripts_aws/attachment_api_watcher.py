import subprocess
import logging
from gec_common import log_config
import os
import time
from datetime import date, datetime, timedelta

while 1 == 1:
    output2 = subprocess.getoutput('curl -Is http://13.127.216.250/in_ddtenders_2023-08-27-09-14-06/4a44c64c-c9ec-4982-a4b9-5cd0316387ea.pdf | head -n 1')
    logging.info(output2)
    logging.info('=================')
    if '405' in output2:
        logging.info("link is working")
    if '502' in output2:
        logging.info("link is not working")
        runStr = "service nginx start"
        os.system(runStr)
        time.sleep(3)
        runStr = "cd /GeC/gecftp/html/temp_files/attachments_api/ && nohup uvicorn attachments:app --reload"
        os.system(runStr)
    if ('405' or '502') not in output2:
        logging.info("I don't know link is working or not")
    time.sleep(3)
