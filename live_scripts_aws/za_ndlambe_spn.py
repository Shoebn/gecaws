from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_ndlambe_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_ndlambe_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element1,tender_html_element2):

    global notice_count

    global notice_data

    notice_data = tender()
 
    notice_data.script_name = 'za_ndlambe_spn'

    performance_country_data = performance_country()

    performance_country_data.performance_country = 'ZA'

    notice_data.performance_country.append(performance_country_data)
 
    notice_data.currency = 'ZAR'
 
    notice_data.main_language = 'EN'
 
    notice_data.procurement_method = 2
 
    notice_data.notice_type = 7

    notice_data.notice_text += tender_html_element1.get_attribute('outerHTML')
    notice_data.notice_text += tender_html_element2.get_attribute('outerHTML')

    notice_data.document_type_description = 'Current Invitations to Bid'

 
    notice_data.notice_url = url

 
    try:
        notice_data.notice_no = tender_html_element1.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if notice_data.notice_no == None:
            pass
    except:
        pass

    try:
        notice_data.local_title =  tender_html_element1.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
        if notice_data.local_title == None:
            pass
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
 
    try:

        document_opening_time = tender_html_element1.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%m/%d/%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
        if notice_data.document_opening_time == None:
            pass
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element1.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+[p][m]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)

    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
 
    try:              

        customer_details_data = customer_details()
 
        customer_details_data.org_name = ' Ndlambe Municipality'

        customer_details_data.org_parent_id=7559363

        customer_details_data.org_country = 'ZA'

        customer_details_data.org_language = 'EN'

        customer_details_data.org_phone = '+27 (46) 604 5500'

        customer_details_data.org_email = "info@ndlambe.gov.za"

        customer_details_data.customer_details_cleanup()

        notice_data.customer_details.append(customer_details_data)

    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:
        for single_record in tender_html_element2.find_elements(By.CSS_SELECTOR, 'ul li p'):

            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text

            attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('.')[-1]

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            logging.info(attachments_data.external_url)
            try:
                attachments_data.file_size = single_record.text.split(' – ')[-1]
            except:
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details 
try:

    th = date.today() - timedelta(1)

    threshold = th.strftime('%Y/%m/%d')

    logging.info("Scraping from or greater than: " + threshold)

    urls = ["https://ndlambe.gov.za/web/current-invitations-to-bid/"] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#post-801 > div > div > table > tbody > tr'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#post-801 > div > div > table > tbody > tr')))
        length = len(rows)
        try:
            for records in range(0,length):
                tender_html_element1  = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#post-801 > div > div > table > tbody > tr')))[records]
                tender_html_element2 = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#post-801 > div > div > table > tbody > tr')))[records+1]
                extract_and_save_notice(tender_html_element1,tender_html_element2)
                if notice_count >= MAX_NOTICES:
                    break
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
        except:
            pass

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
