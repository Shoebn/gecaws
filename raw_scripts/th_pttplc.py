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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "th_pttplc"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'th_pttplc'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'TH'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'THB'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -take local_title in textform and split title dont take "[แก้ไขประกาศครั้งที่ 1]'/"[แก้ไขประกาศครั้งที่ 1]"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take notice_summary_english in textform and dont take "[แก้ไขประกาศครั้งที่ 1]'/"[แก้ไขประกาศครั้งที่ 1]"
    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -เลขที่ประกาศ / เลขที่โครงการ
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-10 > a > h3').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -วันที่ประกาศ :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-lg-7.float-left.title-announce > span:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -ระยะเวลาจำหน่าย:
    # Onsite Comment -take date after "ถึงวันที่" as notice_deadline

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-lg-5.float-left.title-announce2 > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -หลักประกันซอง(ต่อหน่วย) :
    # Onsite Comment -take only "หลักประกันซอง(ต่อหน่วย) :" data

    try:
        notice_data.grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-5.float-left.title-announce2').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -หลักประกันซอง(ต่อหน่วย) :
    # Onsite Comment -take only "หลักประกันซอง(ต่อหน่วย) :" data

    try:
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-5.float-left.title-announce2').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

 # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.container.box-announce-desktop > h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass        
 
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_url = ''https://procurement.pttplc.com/th/Invitation''
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.container > div:nth-child(2) > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
   
# Onsite Field -None
# Onsite Comment -None
    
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.col-lg-7.float-left.title-announce'):
            customer_details_data = customer_details()
        # Onsite Field -หน่วยงานจัดหา:
        # Onsite Comment -take only "หน่วยงานจัดหา:" data

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-7.float-left.title-announce').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'TH'
            customer_details_data.org_language = 'TH'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.card-body > a > h2'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -take lot_title in textform and split title dont take "[แก้ไขประกาศครั้งที่ 1]'/"[แก้ไขประกาศครั้งที่ 1]"

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -take lot_description in textform and dont take "[แก้ไขประกาศครั้งที่ 1]'/"[แก้ไขประกาศครั้งที่ 1]"

            try:
                lot_details_data.lot_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > a > h2').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Envelope collateral (per unit):
        # Onsite Comment -take only "หลักประกันซอง(ต่อหน่วย) :" data

            try:
                lot_details_data.lot_grossbudget_lc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-5.float-left.title-announce2').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ประกาศอื่นๆที่เกี่ยวข้อง
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.row.col-lg-3.float-right >  a'):
            attachments_data = attachments()
        # Onsite Field -ประเภทประกาศ
        # Onsite Comment -click on "ประกาศอื่นๆที่เกี่ยวข้อง" to get attchments

            try:
                attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -click on "ประกาศอื่นๆที่เกี่ยวข้อง" to get attchments and use this selector also "div.col-md-10 > a" for attchments

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://procurement.pttplc.com/th/Invitation'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,4):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Table"]/div[1]/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Table"]/div[1]/div[1]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Table"]/div[1]/div[1]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Table"]/div[1]/div[1]/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    