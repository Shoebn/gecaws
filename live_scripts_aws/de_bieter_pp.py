from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_bieter_pp"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_bieter_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_bieter_pp'
    
    notice_data.main_language = 'DE'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 3
    
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = 'PRELIMINARY INFORMATION'
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.color-primary.card-title-style').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Projektnummer:
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > label').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Veröffentlichungsdatum:
    # Onsite Comment -and for notice_deadline take as threshold date 1 year after the publish_date.

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > div:nth-child(1) > label").text
        publish_date = re.findall('\d+.\d+.\d{4}, \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y, %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Leistungsart:
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Sicherungsleistung/bauaffine Dienstleistung =Service','Bauleistung = Works ','Lieferleistung = Supply', 'Dienstleistung = services ','Architekten- und Ingenieurleistungen = consultancy')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(2)').text.split(":")[1].strip()
        if 'Sicherungsleistung' in notice_contract_type or "bauaffine Dienstleistung" in notice_contract_type or 'Dienstleistung' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        if 'Bauleistung' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        if 'Lieferleistung' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        if 'Architekten- und Ingenieurleistungen' in notice_contract_type:
            notice_data.notice_contract_type = 'Consultancy' 
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    customer_details_data = customer_details()
    try:
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.contracting-authority-style').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass
    customer_details_data.org_country = 'DE'
    customer_details_data.org_language = 'DE'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.resolve-flex-column'):
            attachments_data = attachments()
            attachments_data.file_name = 'NOTICE'
            attachments_data.file_type = '.pdf'
            # Onsite Field -BEKANNTMACHUNG
            # Onsite Comment -None
            external_url = single_record.find_element(By.CSS_SELECTOR, 'button.mat-focus-indicator.mat-tooltip-trigger.details-button-style.mat-stroked-button.mat-button-base.mat-primary').click()
            time.sleep(4)
            page_main.switch_to.window(page_main.window_handles[1])
            attachments_data.external_url = page_main.current_url
            time.sleep(8)
            page_main.close()
            page_main.switch_to.window(page_main.window_handles[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/vorinformationen'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.mat-focus-indicator.mat-tooltip-trigger.mat-paginator-navigation-next.mat-icon-button.mat-button-base')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="project-vertical-container"]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
