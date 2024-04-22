from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_unpd_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_unpd_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

    notice_data.script_name = 'mfa_unpd_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 5
    notice_data.currency = 'USD'
    notice_data.notice_url = url
    notice_data.document_type_description = "TENDERS"
    

    try:  
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,' td.views-field.views-field-field-date ').text
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try: 
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td.views-field.views-field-field-date-2.active').text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td.views-field.views-field-title').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR,'td.views-field.views-field-php > a').get_attribute("href")
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-text-75-1').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'United Nations (UN)'
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = 7753241
        customer_details_data.org_address = '405 East 42nd Street New York, NY 10017'
        customer_details_data.org_phone = '+1-212-963-1127'
        customer_details_data.org_fax = '+1-212-963-9858'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        attachments_data = attachments()
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-url > a').text
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-url > a').get_attribute('href')
        attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR,'td.views-field.views-field-name').text
        notice_data.class_title_at_source = notice_data.category
        cpv_codes = fn.CPV_mapping("assets/mfa_unpd_spn_category.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = 1344862
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.un.org/Depts/ptd/eoi?field_date_2_value%5Bvalue%5D=&field_date_2_value_1%5Bvalue%5D=&field_commodity_group_eoi_rfi_tid=All&items_per_page=40&order=field_date_2&sort=desc']
    try:
        for url in urls:
            fn.load_page(page_main, url, 50)
            logging.info('----------------------------------')
            logging.info(url)
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div/div[2]/div/div/section/div/div[2]/div/div[2]/table/tbody/tr')))
            length = len(rows)                                                                              
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div/div[2]/div/div/section/div/div[2]/div/div[2]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

    except:
        logging.info("No new record")
        break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
