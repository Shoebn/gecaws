from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_stella_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
import os
import csv
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.support.ui import Select
import gec_common.web_application_properties as application_properties

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_stella_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    notice_data.script_name = 'it_stella_spn'
    
    notice_data.notice_type = 4
   
    try:
        published_date = tender_html_element['pubDate']
        published_date = re.findall('\d+/\d+/\d{4}',published_date)[0]
        notice_data.publish_date= datetime.strptime(published_date,'%d/%m/%Y').strftime("%Y/%m/%d")
        logging.info(notice_data.publish_date)
    except:
        pass

    if notice_data.publish_date is not None and notice_data.publish_date >= threshold:
        return

    try:
        notice_data.notice_no = tender_html_element['CIG']
        notice_data.tender_id = notice_data.notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element['DtScadenzaBandoTecnical']
        date_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        time_deadline = re.findall('\d+:\d+:\d+',notice_deadline)[0]
        notice_deadline = date_deadline +" "+ time_deadline
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element['TitoloDocumento']
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        t_id = tender_html_element['IdMsg']
    except Exception as e:
        logging.info("Exception in t_id: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_url = 'https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc='+str(t_id)+'&tipo_doc=BANDO_GARA_PORTALE'
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost'] 
tmp_dwn_dir = application_properties.TMP_DIR#.replace('/',"\\")  #for linux remove --> .replace('/',"\\")
experimental_options = {"prefs": {"download.default_directory": tmp_dwn_dir}}
page_main = fn.init_chrome_driver(arguments=[], experimental_options = experimental_options)
try:
    th = date.today()
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    url = 'https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=regione'
    logging.info(url)
    logging.info('----------------------------------')
    fn.load_page(page_main, url,80)

    clk = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//button[@class="btn btn-primary"]')))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(5)
    pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#listSearch1'))
    pp_btn.select_by_index(2)
    time.sleep(10)

    clk = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pills-tab > li:nth-child(3) > app-pulsante > button > span' )))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(10)
    with open(application_properties.TMP_DIR+"/exportBandiGaraCSV.csv", 'r', encoding="utf8") as f:
        lines = f.readlines()[2:]  # Skip the first two rows
        dict_reader = csv.DictReader(lines)
        BandiGaraCSV = list(dict_reader)
        
    for tender_html_element in BandiGaraCSV:
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    os.remove(application_properties.TMP_DIR+"/exportBandiGaraCSV.csv")
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)