import web_db_connection
import datetime
import time
import json
from datetime import date, datetime, timedelta
import uuid
import os
import shutil
import gec_common.web_application_properties as application_properties
import logging
from gec_common import log_config

connection = web_db_connection.get_conn()
cursor = connection.cursor()
json_File_path = application_properties.GENERATED_JSON_ROOT_DIR + 'cross_check_output'
json_list = os.listdir(json_File_path)

for filename in json_list:
    json_single_File = json_File_path+'/'+filename
    logging.info(json_single_File)

    with open(json_single_File,'r') as single_File :
        json_data = json.load(single_File)

    #try:
    for record in json_data:
        id = str(uuid.uuid4()) + str(datetime.now().strftime("-%Y-%m-%d-%H:%M:%S.%f"))
        update_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        notice_no = record['notice_no']
        notice_deadline = record['notice_deadline']
        publish_date = record['publish_date']
        crawled_at = record['crawled_at']
        script_name = record['script_name']
        notice_type = record['notice_type']
        local_title = record['local_title']
        notice_url = record['notice_url']
        method_name = None

         # Execute the INSERT query with parameterized values
        tender_query = """
            INSERT INTO cross_check_output (
                update_date, id, notice_no, notice_deadline, publish_date,
                script_name, crawled_at, local_title, notice_type, notice_url, method_name
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(tender_query, (
            update_date, id, notice_no, notice_deadline, publish_date,
            script_name, crawled_at, local_title, notice_type, notice_url, method_name
        ))

        # Commit the transaction
        connection.commit()
    try:
        shutil.move(json_single_File, application_properties.GENERATED_JSON_ROOT_DIR + 'uploaded_cross_check_output')
    except:
        json_single_File_new = json_File_path+'/'+'already_exist_'+filename
        os.rename(json_single_File, json_single_File_new)
        shutil.move(json_single_File_new, application_properties.GENERATED_JSON_ROOT_DIR + 'uploaded_cross_check_output')
        pass
    # except Exception as e:
    #     logging.info("Exception in FAILED_JSON_DIR: {}".format(e))
    #     shutil.move(json_single_File, application_properties.GENERATED_JSON_ROOT_DIR + 'failed_cross_check_output')
    #     pass
