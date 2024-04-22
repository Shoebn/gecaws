
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_hudco_spn"
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
import gec_common.Doc_Download_ingate

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_hudco_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_hudco_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.document_type_description = "Current Tenders"
    notice_data.notice_type = 4    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass         
            
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+-\w+-\d+ \d+:\d+ [apAP][mM]', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%b-%y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass            
                
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return                   
        
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+-\w+-\d+ \d+:\d+ [apAP][mM]', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d-%b-%y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass             
            
    try:
        org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text  
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass  
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    except:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#ContentPlaceHolder1_grd_Tender').get_attribute("outerHTML")  
        
    details_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a')
    page_main.execute_script("arguments[0].click();",details_click)
    time.sleep(5)
        
    notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#content').get_attribute("outerHTML")  
    notice_data.notice_url = page_main.current_url          
    notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender ID:")]//following::td[1]').text
    
    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Estimated Tender Value:")]//following::td[1]').text
        notice_data.est_amount = float(est_amount.split('Rs. ')[1])
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"EMD :")]//following::td[1]').text  
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass    
        
    try:
        document_purchase_end_time  = page_main.find_element(By.XPATH, '//*[contains(text(),"Last Date for Document Collection:")]//following::td[1]').text 
        document_purchase_end_time  = re.findall('\d+-\w+-\d+', document_purchase_end_time)[0]
        notice_data.document_purchase_end_time  = notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass    
    
    try:
        document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Technical Bid Opening Date/Time:")]//following::td[1]').text 
        document_opening_time = re.findall('\d+-\w+-\d+', document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d-%b-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass        
    
    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = "Housing And Urban Development Corporation Limited"
        customer_details_data.org_parent_id = 6293380
        org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Number:")]//following::td[1]').text 
        if len(org_phone)>5:
            customer_details_data.org_phone = org_phone

        try:
            org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::td[1]').text  
            if len(org_email)>5:
                customer_details_data.org_email = org_email.split(',')[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__)) 
            pass
    
        try:
            org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Deposit Address:")]//following::td[1]').text  
            if len(org_address)>5:
                customer_details_data.org_address = org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__)) 
            pass
        
        try:
            if len(org_city)>5:
                customer_details_data.org_city = org_city
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__)) 
            pass
        
        try:
            contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Details:")]//following::td[1]').text  
            if len(contact_person)>5:
                customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
            pass
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Work Description:")]//following::td[1]').text  
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        attachments_data = attachments()
        file_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Documents")]//following::td[1]/div/table/tbody/tr[2]/td[1]').text  
        
        attachment_url = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Tender Documents")]//following::td[1]/div/table/tbody/tr[2]/td[2]/a')))
        page_main.execute_script("arguments[0].click();",attachment_url)
        time.sleep(3)
        page_main.switch_to.window(page_main.window_handles[1]) 
        attachments_data.external_url = page_main.current_url  
        attachments_data.file_name = 'Tender Document'

        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass  

        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
        
        page_main.execute_script("window.history.go(-1)")
        page_main.execute_script("window.history.go(-1)")
        time.sleep(3)
        
    except:
        try:
            attachments_data = attachments()
            
            attachments_data.file_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Documents")]//following::td[1]/div/table/tbody/tr[2]/td[1]').text  
            
            attachment_url = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Tender Documents")]//following::td[1]/div/table/tbody/tr[2]/td[2]/a')))
            page_main.execute_script("arguments[0].click();",attachment_url)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
            logging.info("external_url")

            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass  
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__))
            pass            
    
        page_main.execute_script("window.history.go(-1)")
        page_main.execute_script("window.history.go(-1)")
        page_main.execute_script("window.history.go(-1)")
        time.sleep(3)

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://hudco.org.in/TenderHome.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,9):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ContentPlaceHolder1_grd_Tender > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_grd_Tender > tbody > tr')))
                length = len(rows)
                for records in range(1,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_grd_Tender > tbody > tr')))[records]   
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td > div > table > tbody > tr > td:nth-child(2) > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(5)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ContentPlaceHolder1_grd_Tender > tbody > tr:nth-child(2)'),page_check))   
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
    output_json_file.copyFinalJSONToServer(output_json_folder)            
        
