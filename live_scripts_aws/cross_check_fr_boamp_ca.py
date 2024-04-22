from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_fr_boamp_ca"
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
SCRIPT_NAME = "cross_check_fr_boamp_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    notice_data.script_name = 'fr_boamp_ca'
    
    notice_data.notice_type = 7
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.fr-grid-row > span").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date >= threshold:
        return
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-notification > h2 > p > a > span').text
        notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avis n°
    # Onsite Comment -None

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-grid-row > div.fr-checkbox-group > label').text
        notice_data.notice_no = re.findall('\d{2}-\d+',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publié le
    # Onsite Comment -None
    
    notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.fr-container> div > a').get_attribute("href")   
    
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today()
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or lesser than: " + threshold)
    urls = ['https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=10&refine.famille=MAPA&refine.famille=FNS'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):#50
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="toplist"]/li/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="toplist"]/li/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

            try:   
                next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="toplist"]/li/div'),page_check))
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
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
