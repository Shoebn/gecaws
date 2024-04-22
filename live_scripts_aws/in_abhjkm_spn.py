from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_abhjkm_spn"
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
SCRIPT_NAME = "in_abhjkm_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = script_name
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    if 'Corrigendum' in notice_data.notice_title:
        notice_data.notice_type = 16
    try:
        notice_data.local_description= tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass   
    
    
    if notice_data.script_name == 'in_baleswar_spn'  or notice_data.script_name == 'in_jamui_spn' :
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
        notice_data.local_description = None
        notice_data.notice_summary_english = None
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    if notice_data.script_name == 'in_kandhamal_spn' or notice_data.script_name == 'in_hooghly_spn':
        notice_data.local_description = None
        notice_data.notice_summary_english = None
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:
        deadline_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_data.notice_deadline = datetime.strptime(deadline_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender_document'
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5) a").get_attribute('href')
        attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5) a").text.split('(')[1].split(')')[0]
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = org_name
        customer_details_data.org_state = state
        customer_details_data.city = city
        customer_details_data.org_parent_id = parent_id
        
        try:
            customer_details_data.org_address=org_address
        except:
            pass
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

  
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
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
    urls = ["https://angul.nic.in/notice_category/tenders/","https://baleswar.nic.in/notice_category/tenders/","https://bargarh.nic.in/notice_category/tenders/",
           "https://buxar.nic.in/notice_category/tenders/ ","https://hooghly.nic.in/notice_category/tenders/","https://jajpur.nic.in/notice_category/tenders/",
           "https://jamui.nic.in/notice_category/tenders/ ","https://jehanabad.nic.in/en/notice_category/tenders/ ","https://kalahandi.nic.in/notice_category/tenders/",
           "https://kandhamal.nic.in/notice_category/tenders/ ","https://kendujhar.nic.in/notice_category/tenders/ ","https://koraput.nic.in/notice_category/tenders/ ",
           "https://malkangiri.nic.in/notice_category/tenders/ "] 
    for url in urls:
        if urls[0]==url:
            script_name = 'in_angul_spn'
            city = 'angul'
            state = 'Odisha'
            org_name = 'District of Angul'
            parent_id = 35790
        if urls[1]==url:
            script_name = 'in_baleswar_spn'
            city = 'baleswar'
            state = 'Odisha'
            org_name = 'District of baleswar'
            parent_id = 35798
        if urls[2]==url:
            script_name = 'in_bargarh_spn'
            city = 'bargarh'
            state = 'Odisha'
            org_name = 'District of bargarh'
            parent_id = 35805
        if urls[3]==url:
            script_name = 'in_buxar_spn'
            city = 'buxar'
            state = 'Bihar'
            org_name = 'District of buxar'
            parent_id = 35830
        if urls[4]==url:
            script_name = 'in_hooghly_spn'
            city = 'hooghly'
            state = 'West Bengal'
            org_name = 'District of hooghly'
            parent_id = 35952
        if urls[5]==url:
            script_name = 'in_jajpur_spn'
            city = 'jajpur'
            state = 'Odisha'
            org_name = 'District of jajpur '
            parent_id = 36018
        if urls[6]==url:
            script_name = 'in_jamui_spn'
            city = 'jamui'
            state = 'Bihar'
            org_name = 'District of jamui '
            parent_id = 36021
        if urls[7]==url:
            script_name = 'in_jehanabad_spn'
            city = 'jehanabad'
            state = 'Bihar'
            org_name = 'District of jehanabad '
            parent_id = 36022
            
        if urls[8]==url:
            script_name = 'in_kalahandi_spn'
            city = 'kalahandi'
            state = 'Odisha'
            org_name = 'District of kalahandi'
            parent_id = '36028'
            parent_id = int(parent_id)
            
        if urls[9]==url:
            script_name = 'in_kandhamal_spn'
            city = 'kandhamal'
            state = 'Odisha'
            org_name = 'District of kandhamal'
            parent_id = 36029
        if urls[10]==url:
            script_name = 'in_kendujhar_spn'
            city = 'kendujhar'
            state = 'Odisha'
            org_name = 'District of kendujhar '
            parent_id = 36034
        if urls[11]==url:
            script_name = 'in_koraput_spn'
            city = 'koraput'
            state = 'Odisha'
            org_name = 'District of koraput '
            parent_id = 36044
        if urls[12]==url:
            script_name = 'in_malkangiri_spn'
            city = 'malkangiri'
            state = 'Odisha'
            org_name = 'District of malkangiri '
            parent_id = 36061
            
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#row-content > div > table > tbody > tr '))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#row-content > div > table > tbody > tr ')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#row-content > div > table > tbody > tr ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#row-content > div > table > tbody > tr'),page_check))
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
