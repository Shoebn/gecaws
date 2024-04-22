from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_suratmunicipal_spn"
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


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_suratmunicipal_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'INR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.script_name = "in_suratmunicipal_spn"
    
    notice_data.notice_type = 4
    
    notice_data.document_type_description = "ACTIVE TENDERS"
          
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.tender-description').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' div.mar-t20.mar-b10 > span:nth-child(1)').text
        publish_date = re.findall('\d+-\d+-\d{4} \d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, ' div.mar-t20.mar-b10 > span:nth-child(1)').text
        document_purchase_start_time = re.findall('\d+-\d+-\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, ' div.mar-t20.mar-b10 > span:nth-child(3)').text.split("End Date:")[1]
        document_purchase_end_time = re.findall('\d+-\d+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, ' div.mar-t20.mar-b10 > span:nth-child(3)').text.split("End Date:")[1]
        notice_deadline = re.findall('\d+-\d+-\d{4} \d{2}:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_url = page_main.find_element(By.CSS_SELECTOR, " a.button-control").click()
        time.sleep(10)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'section.inner-page-contents').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::div[1]').text
        notice_data.local_description = local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description[:4500]) 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Notice Number")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        document_cost = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Fees (in Rupees)")]//following::div[1]').text
        document_cost = re.sub("[^\d+]",'',document_cost)
        notice_data.document_cost = float(document_cost.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Estimated Amount (in Rupees)")]//following::div[1]').text
        est_amount = re.sub("[^\d+]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        earnest_money_deposit = page_main.find_element(By.XPATH, '//*[contains(text(),"Earnest Money Deposit (in Rupees)")]//following::div[1]').text
        notice_data.earnest_money_deposit = earnest_money_deposit 
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        document_opening_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Probable Date of opening")]//following::div[1]').text
        document_opening_time = re.findall('\d+ \w+, \d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %B, %Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
            
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "SURAT MUNICIPAL CORPORATION"
        
        try:
            org_address1 = page_main.find_element(By.XPATH, '//*[contains(text(),"Issuing Authority")]//following::div[1]').text
            org_address2 = page_main.find_element(By.XPATH, '//*[contains(text(),"Filled tender to be submitted to")]//following::div[1]').text
            customer_details_data.org_address = org_address1+" "+org_address2
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_state = "Gujarat"
        
        org_parent_id ="7527899"
        customer_details_data.org_parent_id = int(org_parent_id)
        
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/section/section/div[2]/div/div[2]/div/div[2]/ol/li[1]'))).text

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)      
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
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.suratmunicipal.gov.in/Information/Tender/Tenders'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):#5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/section/section/div[2]/div/div[2]/div/div[2]/ol/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section/section/div[2]/div/div[2]/div/div[2]/ol/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section/section/div[2]/div/div[2]/div/div[2]/ol/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/section/section/div[2]/div/div[2]/div/div[2]/ol/li'),page_check))
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
