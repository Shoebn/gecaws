from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_altoad_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_altoad_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    notice_data.script_name = 'it_altoad_spn'
    
    notice_data.notice_type = 4
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.publishedAt").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date >= threshold:
        return
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.subject > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'span.protocolId').text
        notice_data.tender_id = notice_data.notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass        
        
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)

try:
    th = date.today()
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or lesser than: " + threshold)
    urls = ['https://www.bandi-altoadige.it/index/index/page/1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,20):#20
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Contenuto"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'li:nth-child(12) > a')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Contenuto"]/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Done cross checked total notice which has to be downloaded {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
