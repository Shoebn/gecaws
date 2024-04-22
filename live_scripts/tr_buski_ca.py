from gec_common.gecclass import *
import logging
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
from selenium.webdriver.support.ui import Select
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tr_buski_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global notice_type
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'TRY'
    notice_data.main_language = 'TR'
    notice_data.script_name = 'tr_buski_ca'

    notice_data.notice_type = 7

    notice_data.procurment_method = 2

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' td:nth-child(1)').get_attribute('innerHTML')
    except:
        pass
        
    notice_data.notice_url = url
    notice_data.document_type_description = 'Sonuçlanmış İhaleler'
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').get_attribute('innerHTML')
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
       
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').get_attribute('innerHTML')
        notice_data.publish_date = datetime.strptime(publish_date, '%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'BUSKİ Genel Müdürlüğü'
        customer_details_data.org_parent_id = '7768776'
        customer_details_data.org_country = 'TR'
        customer_details_data.org_language = 'TR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'td:nth-child(6) a'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')
            time.sleep(5)
            attachments_data.file_name = 'Sonuç Dosyası'
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass 

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()

        lot_details_data.lot_title = notice_data.local_title
        lot_details_data.lot_title_english = notice_data.notice_title
        
        notice_data.is_lot_default = True

        try:
            award_details_data = award_details()
            try:
                award_details_data.award_date = datetime.strptime(publish_date, '%d.%m.%Y').strftime('%Y/%m/%d')
            except:
                pass

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').get_attribute('innerHTML')
        if "Kiraya Verilme" in notice_data.contract_type_actual:
            notice_data.notice_contract_type="Service"
        elif  "Mal Alımı" in notice_data.contract_type_actual or "Yapım" in notice_data.contract_type_actual: 
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date)  + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    urls = ['https://www.buski.gov.tr/Ihale/SonuclanmisIhaleler'] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.app-container.w-100.d-flex.flex-column.flex-xl-row.p-0 > div.cnt-main.d-flex.flex-column.flex-grow-1.flex-shrink-1 > div.cnt-middle.px-0.px-md-1.px-xl-3.d-flex.flex-column.flex-xl-row.flex-grow-1 > div > div > div > table > tbody > tr')))
            length = len(rows) 
            for records in range(0,length):#length
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div.app-container.w-100.d-flex.flex-column.flex-xl-row.p-0 > div.cnt-main.d-flex.flex-column.flex-grow-1.flex-shrink-1 > div.cnt-middle.px-0.px-md-1.px-xl-3.d-flex.flex-column.flex-xl-row.flex-grow-1 > div > div > div > table > tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
