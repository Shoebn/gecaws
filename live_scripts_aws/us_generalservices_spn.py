from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "us_generalservices_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.th_Doc_Download as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "us_generalservices_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'us_generalservices_spn'
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.strip() 
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.strip() 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass    
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#wrapper > div.card').get_attribute("outerHTML")                                

    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.strip() 
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass            

    try:
        notice_no_click = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(4) > a")))
        page_main.execute_script("arguments[0].click();",notice_no_click)        
        time.sleep(2)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#wrapper > div.card'))).get_attribute("outerHTML") 
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass           

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Commodity Description")]//following::span[1]').text.strip() 
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass    
    
    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Amount")]//following::span[1]').text.strip() 
        est_amount = est_amount.split('$')[1].strip()
        notice_data.est_amount = float(est_amount.replace(',',''))
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass   
    
    try:
        tender_contract_start_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Start")]//following::span[1]').text.strip()   
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date, '%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')  
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass       
    
    try:
        tender_contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"End")]//following::span[1]').text.strip()   
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date, '%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')  
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass       
    
    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Quantity of the service")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass         

    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'

        try:
            customer_details_data.org_name = org_name.split('-')[1].strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass          
        
        try:
            contact_person = page_main.find_element(By.XPATH,'//*[contains(text(),"Buyer")]//following::span[1]').text
            if len(contact_person)>=3:
                customer_details_data.contact_person = contact_person
            else:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, """//*[contains(text(),"Contractor's Name")]//following::span[1]""").text 
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass      
        
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH,'//*[contains(text(),"Address")]//following::span[1]').text  
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass          
                    
        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH,'//*[contains(text(),"City")]//following::span[1]').text  
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass          
        
        try:
            customer_details_data.org_state = page_main.find_element(By.XPATH,'//*[contains(text(),"State/Province")]//following::span[1]').text  
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass             
        
        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH,'//*[contains(text(),"Zip")]//following::span[1]').text  
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass            
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        

    try:         
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#ContentPlaceHolder1_gvFileList > tbody > tr')[1:]: 
            attachments_data = attachments()
            
            file_name = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(3)").text   
            attachments_data.file_name = file_name.split('.')[0]

            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR,"td:nth-child(1)").text  
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(3) > a"))) 
            page_main.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass    
    
    try:
        Back_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ContentPlaceHolder1_lbBack")))
        page_main.execute_script("arguments[0].click();",Back_click)        
        time.sleep(5)
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_ContentPlaceHolder1_rgProcurements_ctl00"]/tbody/tr')))
    except Exception as e:
        logging.info("Exception in Back_click: {}".format(type(e).__name__)) 
        pass    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) + str(notice_data.notice_url)  
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
    urls = ["https://www.generalservices.state.nm.us/state-purchasing/active-itbs-and-rfps/active-procurements/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        Accept_click = page_main.find_element(By.XPATH, "//button[contains(@class,'cmplz-btn cmplz-accept')]").click()
        time.sleep(5)

        iframe = page_main.find_element(By.CSS_SELECTOR,'#edh-iframe')
        page_main.switch_to.frame(iframe)
        time.sleep(3)
        
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_ContentPlaceHolder1_rgProcurements_ctl00"]/tbody/tr'))).text 
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_rgProcurements_ctl00"]/tbody/tr')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_rgProcurements_ctl00"]/tbody/tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)