import glob
import logging
from gec_common import log_config
import sys
import os
from datetime import date, datetime, timedelta
import db_connection
import re
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s, %(levelname)s: %(message)s")


def script_get_conn():
    DATABASE_HOST = "prod-gec-db.chsqqj3urp6j.ap-south-1.rds.amazonaws.com"
    DATABASE_NAME = "gecuserdb"
    DATABASE_USERNAME = "gecpgadmin"
    DATABASE_PASSWORD = "g3cStrongPass22"
    DATABASE_PORT = "5432"
    db = psycopg2.connect(user=DATABASE_USERNAME,
                          password=DATABASE_PASSWORD,
                          database=DATABASE_NAME,
                          host=DATABASE_HOST)
    return db
th = date.today() - timedelta(1)
logging.basicConfig(level=logging.INFO)

JSON_PATH = "/GeC/gecftp/uploaded_json"
LOG_PATH = "/GeC/gecftp/logs"
def log_status(log_file_names):
    script_execution_start_time = 'NA'
    script_execution_end_time = 'NA'
    result = 'NA'
    try:
        for log_file_name in log_file_names:
            file = open(log_file_name, mode="r", encoding="latin-1")
            fread = file.read()
            for line in fread.split('\n'):
                if 'INFO: Scraping from or greater than:' in line:
                    script_execution_start_time = line.split(',')[0]
                elif 'Finished processing.' in line:
                    script_execution_end_time = line.split(',')[0]
            finished = fread.count("Finished processing")
            error = fread.count("Message:")
            error2 = fread.count('No such file')
            no_record = fread.count('No new record')
            no_next_page = fread.count('Exception in next_page')
            file.close()
            if no_record > 0:
                result = 'No new record'
            elif error > 0 or error2 > 0:
                result = 'Error'
            elif no_next_page > 0:
                result = 'Next page exception'
            elif  finished  > 0:
                result = 'Done'       
            
            else:
                result = 'Not Completed'
    except:            
        logging.info("log_file not found:" + str(log_file_name))
        result = 'Log Not Found'
    return result,script_execution_start_time,script_execution_end_time


def count_notices(xml_file_names):
    main_count = 0
    main_countca = 0
    main_countrei = 0
    main_countspn = 0
    main_countpp = 0
    main_countprj = 0
    main_countother = 0


    words = ["additional_source_id", '"notice_type": 0', '"notice_type": 1', '"notice_type": 2', '"notice_type": 3', '"notice_type": 4', '"notice_type": 5', '"notice_type": 6','"notice_type": 7', '"notice_type": 8', '"notice_type": 9', '"notice_type": 10', '"notice_type": 11', '"notice_type": 12', '"notice_type": 13', '"notice_type": 14', '"notice_type": 15', '"notice_type": 16']
    for word in words:
        for xml_file in xml_file_names:
            file = open(xml_file, mode="r", encoding="utf8")
            if word == 'additional_source_id':
                result = file.read().count(word)
                file.close()
                main_count = main_count + result
            elif word == '"notice_type": 4' or word == '"notice_type": 9':
                resultspn = file.read().count(word)
                file.close()
                main_countspn = main_countspn + resultspn
            elif word == '"notice_type": 5'or word == '"notice_type": 6' or word == '"notice_type": 8':
                resultrei = file.read().count(word)
                file.close()
                main_countrei = main_countrei + resultrei
            elif word == '"notice_type": 7':
                resultca = file.read().count(word)
                file.close()
                main_countca = main_countca + resultca
            elif word == '"notice_type": 3' or word == '"notice_type": 2':
                resultpp = file.read().count(word)
                file.close()
                main_countpp = main_countpp + resultpp
            elif word == '"notice_type": 10':
                resultprj = file.read().count(word)
                file.close()
                main_countprj = main_countprj + resultprj
            else:
                resultother = file.read().count(word)
                file.close()
                main_countother = main_countother + resultother

    return main_count, main_countspn, main_countrei, main_countca, main_countpp, main_countprj,main_countother

not_executed = []
error = []
not_completed = []
completed = []
no_record = []
in_not_executed = []
in_error = []
in_not_completed = []
in_completed = []
in_no_record = []
no_next_page = []
in_no_next_page = []
def script_health(date_formatted,dataid, script_name):    
    xml_file_name_wildcard = "{}/{}_{}*.json".format(JSON_PATH, script_name, date_formatted)
    logging.info(xml_file_name_wildcard)
    json_file_names = glob.glob(xml_file_name_wildcard)
    logging.info(json_file_names)
    date_formatted_logs = date_formatted.strftime("%d-%m-%Y")
    log_file_name_wildcard = "{}/{}-{}.log".format(LOG_PATH, script_name, date_formatted_logs)    
    logging.info("log_file_name_wildcard: " +  str(log_file_name_wildcard))
    log_file_names = glob.glob(log_file_name_wildcard)
    logging.info("log_file_names: " + str(log_file_names))

    notice_count = count_notices(json_file_names)
    if len(log_file_names) < 1:
        status_message = 'Not Executed'
    else:
        status_message = log_status(log_file_names)[0]
    logging.info(status_message)
    date_formatted = date_formatted.strftime("%Y-%m-%d")
    result = {
        "dataid" : dataid,
        "script_name" : script_name,
        "visit_date" : date_formatted,
        "total_notices" : notice_count[0],
        "spn" : notice_count[1], 
        "rei" : notice_count[2], "ca" : notice_count[3], "pp" : notice_count[4], 
        "prj" : notice_count[5],
        "other" : notice_count[6],
        "status_message" : status_message,
        "json_file_names" : str(json_file_names).replace("'",""),
        "script_execution_start_time" : log_status(log_file_names)[1],
        "script_execution_end_time" : log_status(log_file_names)[2],
        "log_file_names" : str(log_file_names).replace("'","")
    }
    
    if 'Not Executed' in status_message:
        not_executed.append(script_name)

    if 'Error' in status_message:
        error.append(script_name)

    if 'Done' in status_message:
        completed.append(script_name)

    if 'Not Completed' in status_message:
        not_completed.append(script_name)
    
    if 'No new record' in status_message:
        no_record.append(script_name)

    if 'Next page exception' in status_message:
        no_next_page.append(script_name)
    return result

def get_yesterday_formatted():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def get_scripts():
    connection = None
    db_cursor = None

    try:
        connection = script_get_conn()
        db_cursor = connection.cursor()
        db_cursor.execute("select appsource_dataid,internal_code from app_sources where status in (1,2,4,13,15,16,17)")
        db_results = db_cursor.fetchall()
        return db_results
    except Exception as e:
        logging.error(e)
    finally:
        if db_cursor is not None:
            db_cursor.close()
        if connection is not None:
            connection.close()        
def log_scraping_result(script_log):
    connection = db_connection.get_conn()
    db_cursor = connection.cursor()

    db_cursor.execute("delete from scraping_log where internal_code = '{}' and visit_date = '{}'".format(script_log["script_name"], script_log["visit_date"]))

    logging.info("Saving record: {}".format(script_log))
    query = "INSERT INTO scraping_log(dataid,internal_code,visit_date,notice_count,SPN,REI,CA,PP,PRJ,other,log_status,json_file_name_list,log_path,script_execution_start_time,script_execution_end_time,cross_check_status) " \
            "VALUES ({},'{}','{}',{},{},{},{},{},{},{},'{}','{}','{}','{}','{}','{}')"\
        .format(script_log["dataid"],script_log["script_name"], script_log["visit_date"], script_log["total_notices"],
                script_log["spn"], script_log["rei"], script_log["ca"], script_log["pp"], script_log["prj"], script_log["other"],script_log["status_message"],script_log["json_file_names"],
                script_log["log_file_names"],script_log["script_execution_start_time"],script_log["script_execution_end_time"],'to_be_checked')
    db_cursor.execute(query)
    connection.commit()
    db_cursor.close()



date_formatted = get_yesterday_formatted()
date_formatted = th

scraping_scripts = get_scripts()
try:
    for scraping_script in scraping_scripts:
        logging.info(scraping_script)
        script_health_result = script_health(date_formatted, scraping_script[0], scraping_script[1])
        log_scraping_result(script_health_result)
except Exception as e:
    pass
    raise e
finally:
    logging.info('finally')
    msg = MIMEMultipart()
    gladdr = "dgreport@dgmarket.com"
    msg['Subject'] =  'Script Health GEC Server: '+str(th)
    body =  '<u>' + '<strong>' + 'Script Health Server Report dated: '+str(th)+ '</strong>' + '</u><br/>'
    body += '<br/>'
    body += '<br/>'
    body = '<strong>' + 'Not Executed: ' + '</strong><br/>' +str(not_executed)
    body += '<br/>'
    body += '<br/>'
    body += '<strong>' + 'Error list: ' + '</strong><br/>' + str(error)
    body += '<br/>'
    body += '<br/>'
    body += '<strong>' + 'Not Completed: ' + '</strong><br/>' + str(not_completed)
    body += '<br/>'
    body += '<br/>'
    body += '<strong>' + 'Completed: ' + '</strong><br/>' + str(completed)
    body += '<br/>'
    body += '<br/>'
    body += '<strong>' + 'No new record: ' + '</strong><br/>' + str(no_record)
    body += '<br/>'
    body += '<br/>'
    body += '<strong>' + 'Next page exception: ' + '</strong><br/>' + str(no_next_page)
    body += '<br/>'
    body += '<br/>'
    body +=  '<u>' +'<strong>' + 'End of Report dated: '+str(th) + '</strong>'+ '</u><br/>'
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(gladdr, "dgmarket@123")

    text = msg.as_string()
    toaddr = "jenil.a@globalecontent.com,shoeb.n@globalecontent.com,pooja.s@globalecontent.com,jitendar.j@globalecontent.com,varun@globalecontent.com,prakash@globalecontent.com,akanksha@globalecontent.com"
    msg['To'] = toaddr
    server.sendmail(gladdr, toaddr.split(','), text)
    server.quit()
    
    # msg = MIMEMultipart()
    # gladdr = "dgreport@dgmarket.com"
    # msg['Subject'] =  'Script Health GEC Server India: '+str(th)
    # body =  '<u>' + '<strong>' + 'Script Health Server India Report dated: '+str(th) + '</strong>' + '</u><br/>'
    # body += '<br/>'
    # body += '<br/>'
    # body = '<strong>' + 'Not Executed: ' + '</strong><br/>' +str(in_not_executed)
    # body += '<br/>'
    # body += '<br/>'
    # body += '<strong>' + 'Error list: ' + '</strong><br/>' + str(in_error)
    # body += '<br/>'
    # body += '<br/>'
    # body += '<strong>' + 'Not Completed: ' + '</strong><br/>' + str(in_not_completed)
    # body += '<br/>'
    # body += '<br/>'
    # body += '<strong>' + 'Completed: ' + '</strong><br/>' + str(in_completed)
    # body += '<br/>'
    # body += '<br/>'
    # body += '<strong>' + 'No new record: ' + '</strong><br/>'+ str(in_no_record)
    # body += '<br/>'
    # body += '<br/>'
    # body += '<strong>' + 'Next page exception: ' + '</strong><br/>' + str(in_no_next_page)
    # body += '<br/>'
    # body += '<br/>'
    # body +=  '<u>' + '<strong>' + 'End of Report dated: '+str(th) + '</strong>' + '</u><br/>'
    # msg.attach(MIMEText(body, 'html'))
    # server = smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # server.login(gladdr, "dgmarket@123")

    # text = msg.as_string()
    # toaddr = "jenil.a@globalecontent.com,shoeb.n@globalecontent.com,pooja.s@globalecontent.com,jitendar.j@globalecontent.com,varun@globalecontent.com,prakash@globalecontent.com,akanksha@globalecontent.com"
    # msg['To'] = toaddr
    # server.sendmail(gladdr, toaddr.split(','), text)
    # server.quit()

