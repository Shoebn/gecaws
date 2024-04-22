
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_nrl_spn"
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


from datetime import datetime, timedelta


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_nrl_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_nrl_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.document_type_description = "Current Open Tender"
    notice_data.notice_type = 4
      

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass              

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass          
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        pass        
            
    Tender_No_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a')
    page_main.execute_script("arguments[0].click();",Tender_No_click)
    time.sleep(5)
    notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#aspnetForm').get_attribute("outerHTML")  
    notice_data.notice_url = page_main.current_url
    logging.info(notice_data.notice_url)
        
    try:
        notice_data.category = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Type")]//following::div[1]').text 
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass          

    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"EMD")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass      

    try:
        document_opening_time_text = page_main.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_divcorrigendum').text 
    except Exception as e:
        logging.info("Exception in document_opening_time_text: {}".format(type(e).__name__))
        pass 

    try:
        if 'Corrigendum' in document_opening_time_text:
            document_opening_time = document_opening_time_text.split('Opening of Bid')[1].strip()
            document_opening_time = re.findall('\d+ \w+ \d+', document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d %b %Y').strftime('%Y-%m-%d')
            notice_deadline = document_opening_time_text.split('Bid Submission end date')[1].split('\n')[0]
            notice_deadline = notice_deadline.replace('Time :','')
            notice_deadline = re.findall('\d+ \w+ \d+ \d+:\d+ [apAP][mM]', notice_deadline)[0]
            notice_deadline = datetime.strptime(notice_deadline, '%d %b %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            notice_deadline = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid Submission end date")]//following::td[1]').text
            notice_deadline = notice_deadline.replace('Time :','')
            notice_deadline = re.findall('\d+ \w+ \d+ \d+:\d+ [apAP][mM]', notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d %b %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass             

        try:
            document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Bid(Technical) opening date")]//following::td[1]').text 
            document_opening_time = re.findall('\d+ \w+ \d+', document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d %b %Y').strftime('%Y-%m-%d')
        except:
            try:
                document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Opening of Bid")]//following::td[1]').text  
                document_opening_time = re.findall('\d+ \w+ \d+', document_opening_time)[0]
                notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d %b %Y').strftime('%Y-%m-%d')            
            except Exception as e:
                logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
                pass     

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return    

    try:              
        if 'Corrigendum' in document_opening_time_text:
            attachments_data = attachments()
            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_divaddendum > div.col-3.inline-block > p > a').get_attribute('href') 

            attachments_data.file_name = 'tender_documents'
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass          
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_divattachment > div.col-3.inline-block > p > a').get_attribute('href') 
        attachments_data.file_name = 'tender_documents'
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass          

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    page_main.execute_script("window.history.go(-1)")
    time.sleep(3)    
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "NUMALIGARH REFINERY LIMITED"
        customer_details_data.org_parent_id = 7248246
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.nrl.co.in/Internal_TenderNewstatic.aspx?PageID=1"]
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            for page_no in range(2,9):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ctl00_ContentPlaceHolder1_gv_tender > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_gv_tender > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_gv_tender > tbody > tr')))[records]   
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                            break
                       
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
                    try:   
                        next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,f'td > table > tbody > tr > td:nth-child({page_no}) > a')))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ctl00_ContentPlaceHolder1_gv_tender > tbody > tr:nth-child(2)'))).text  
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ctl00_ContentPlaceHolder1_gv_tender > tbody > tr:nth-child(2)'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
        except Exception as e:
            logging.info('No new record')
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)            
            
