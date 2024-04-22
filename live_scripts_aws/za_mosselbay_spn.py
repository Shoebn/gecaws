from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_mosselbay_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_mosselbay_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

# --------------------------------------------------------------------------------------------------------------------------------
# for tender details go to URL: "https://www.mosselbay.gov.za/procurement-index" and select "Tenders Available" 
# note: use VPN for this source ( south africa )

# ---------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'za_mosselbay_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'za'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'ZAR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = 'Tenders Available'
    
    # Onsite Field -Ref. No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td.dtr-control').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date Opened
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Action
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(5) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:    
        ACCEPT = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.botton > button:nth-child(1)'))).click()    
        time.sleep(2)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-md-12.p-5.about-info > div > div.col-md-8').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description :")]').text.split("Description :")[1].strip()
        notice_data.notice_summary_english =notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'mosselbay municipality'
        customer_details_data.org_parent_id = '77292431'
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.btn.view'):
            
        # Onsite Field -None
        # Onsite Comment -split only file_name for ex. "89-2023-2024 Advert" , ref_url : "https://www.mosselbay.gov.za/tender-available-view/fe62f77f-a968-4c85-ab20-4354f0114ef1" , do not take "Email Document" named button

            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')
            
            attachments_data.file_name = single_record.text
            
             # Onsite Field -None
        # Onsite Comment -split only file_type

            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            if attachments_data.external_url != None:
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.mosselbay.gov.za/procurement-index"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        ACCEPT = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' div.botton > button:nth-child(1)'))).click()    
        time.sleep(2)
        
        tender_available = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="showtab2"]/center/img'))).click()    
        time.sleep(2)
        
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/section[4]/div/div[2]/div/div/div[1]/div/div/div/div/table/tbody/tr')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/section[4]/div/div[2]/div/div/div[1]/div/div/div/div/table/tbody/tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break


    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
