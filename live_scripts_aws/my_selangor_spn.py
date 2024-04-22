
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "my_selangor_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "my_selangor_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'my_selangor_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MY'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'MYR'
    notice_data.main_language = 'MS'
    notice_data.procurement_method = 2

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td > small').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
    notice_data.notice_title = notice_data.local_title

    try:
        document_cost = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.document_cost =  float(document_cost.split('RM')[1].strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass    
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#container').get_attribute("outerHTML")  

    try:
        publish_date = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tarikh Iklan")]//following::td[1])').text
        publish_date  = publish_date.split('-')[0].strip()
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tarikh Tutup")]//following::td[1])').text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass   
    try:
        document_opening_time = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tarikh Jual")]//following::td[1])').text    
        document_opening_time = document_opening_time.split('-')[0].strip()
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %b %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass    

    try:
        document_purchase_start_time = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tarikh Jual")]//following::td[1])').text    
        document_purchase_start_time = document_opening_time.split('-')[0].strip()
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d %b %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass    
    try:
        document_purchase_end_time = page_details.find_element(By.XPATH, '(//*[contains(text(),"Tarikh Jual")]//following::td[1])').text    
        document_purchase_end_time = document_purchase_end_time.split('-')[1].strip()
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d %b %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, '(//*[contains(text(),"Petender")]//following::td[1])').text 
        try:
            Pegawai_Bertanggungjawab_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Pegawai Bertanggungjawab")])[1]')))  
            page_details.execute_script("arguments[0].click();",Pegawai_Bertanggungjawab_click)
            logging.info("Pegawai_Bertanggungjawab_click")
            time.sleep(5)                        
            notice_data.notice_text += WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#container'))).get_attribute("outerHTML")  
        except Exception as e:
            logging.info("Exception in Pegawai_Bertanggungjawab_click: {}".format(type(e).__name__)) 
            pass          
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Nama")]//following::td[1])').text 
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass          
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"E-mel")]//following::td[1])').text 
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass          
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"No. Tel")]//following::td[1])').text 
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass          
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '(//*[contains(text(),"Jabatan")]//following::td[4])').text 
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass       
        customer_details_data.org_country = 'MY'
        customer_details_data.org_language = 'MS'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       
    
    try:
        Dokumen_Meja_Terkawal_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Dokumen Meja Terkawal")])[1]')))  
        page_details.execute_script("arguments[0].click();",Dokumen_Meja_Terkawal_click)
        logging.info("Dokumen_Meja_Terkawal_click")
        time.sleep(5)
        notice_data.notice_text += WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#container'))).get_attribute("outerHTML")  
    except Exception as e:
        logging.info("Exception in Dokumen_Meja_Terkawal_click: {}".format(type(e).__name__)) 
        pass     
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#tf-doc1 > table > tbody > tr'):
            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute('href') 
            attachments_data = attachments()
            attachments_data.external_url = external_url        
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            if len(file_name)>7:
                attachments_data.file_name = file_name
            else:
                attachments_data.file_name = 'Tender Document'
            try:
                attachments_data.file_type = external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass          
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass           
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
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://tender.selangor.my/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(3)

        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#DataTables_Table_0 > tbody > tr'))).text  
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#DataTables_Table_0 > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#DataTables_Table_0 > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
            
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'ul > li.next > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#DataTables_Table_0 > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
