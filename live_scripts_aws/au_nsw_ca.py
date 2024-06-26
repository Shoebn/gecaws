
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_nsw_ca"
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
import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_nsw_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'au_nsw_ca'
    notice_data.main_language = 'EN'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'AUD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    


    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > div > div:nth-child(2) > h2').text
    notice_data.notice_title = notice_data.local_title

    details_text = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div:nth-child(2) > p').text
    
    notice_data.notice_no = details_text.split('CAN ID')[1].split('\n')[0].strip()
    
    try:
        publish_date = details_text.split('Published')[1].split('\n')[0].strip()
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass   

    grossbudgetlc = details_text.split('(including GST) $')[1].split('(')[0].strip() 
    notice_data.grossbudgetlc = float(grossbudgetlc.replace(',',''))
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > div > div:nth-child(2) > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.wrapper > div.main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url    
            
    try:
        category = page_details.find_element(By.XPATH, '//*[contains(text()," Contract Award Notice ID")]//following::div[2]').text  
        notice_data.category = category.split('Category')[1].strip()
        cpv_codes = fn.CPV_mapping("assets/au_nsw_ca_category.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass        
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = details_text.split('Agency')[1].split('\n')[0].strip()    
        customer_details_text = page_details.find_element(By.XPATH, '//*[contains(text()," Contract Award Notice Details ")]//following::div[1]').text  
        customer_details_data.org_city = customer_details_text.split('Town/City')[1].split('\n')[0].strip()
        customer_details_data.org_state = customer_details_text.split('State/Territory')[1].split('\n')[0].strip()
        customer_details_data.postal_code = customer_details_text.split('Postcode')[1].split('\n')[0].strip()    
        customer_details_data.org_country = customer_details_text.split('Country')[1].split('\n')[0].strip()    
        Street_Address = customer_details_text.split('Street Address')[1].split('\n')[0].strip()
        
        customer_details_data.org_address = f'{Street_Address} {customer_details_data.org_city} {customer_details_data.postal_code} {customer_details_data.org_country}'
        customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email Address")]//following::a[1]').text      
        customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#CN-AgencyContact').text      
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass    

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_title = notice_data.notice_title
        lot_details_data.lot_number = 1

        try:
            contract_start_date = details_text.split('Contract Period')[1].split('\n')[0].strip()
            contract_start_date = contract_start_date.split('to')[0].strip()
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d-%b-%Y').strftime('%Y/%m/%d') 
            notice_data.tender_contract_start_date = lot_details_data.contract_start_date
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            contract_end_date = details_text.split('Contract Period')[1].split('\n')[0].strip()
            contract_end_date = contract_end_date.split('to')[1].strip()
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d-%b-%Y').strftime('%Y/%m/%d')
            notice_data.tender_contract_end_date = lot_details_data.contract_end_date
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            award_details_data = award_details()
            award_details_data.bidder_name = details_text.split('Contractor Name')[1].split('\n')[0].strip()
            award_details_data.address = customer_details_data.org_address
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_criteria_text = page_details.find_element(By.CSS_SELECTOR, 'div > div.table-box > div > table > tbody > tr').text
        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.table-box > div > table > tbody > tr')[1:]:
                lot_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                try:
                    lot_criteria_data = lot_criteria()
                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight.split('%')[0].strip())
                    lot_criteria_data.lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except:
                    lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                    if '%' in lot_criteria_title:
                        lot_criteria_data = lot_criteria()
                        lot_criteria_data.lot_criteria_title = lot_criteria_title
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_title.split(':')[1].split('%')[0].strip())

                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
        except Exception as e:
            logging.info("Exception in lot_criteria_data: {}".format(type(e).__name__)) 
            pass

        lot_details_data.lot_award_date = notice_data.publish_date
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.tenders.nsw.gov.au/?event=public.CN.search&_gl=1*1c9z6w1*_ga*Mjg5Njk3Njg2LjE3MTIwNTQ5ODc.*_ga_FCJTC9BDBG*MTcxMjA2MjEzNy4yLjEuMTcxMjA2MjIwOC42MC4wLjA"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        Search_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Search")])[10]'))) 
        page_main.execute_script("arguments[0].click();",Search_click)
        logging.info("Search_click")
        
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#main-content > div.list-box > div.list-box-inner.list-box-inner-first'))).text  
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#main-content > div.list-box > div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#main-content > div.list-box > div')))[records] 
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#main-content > div.list-box > div.list-box-inner.list-box-inner-first'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#main-content > div.list-box > div.list-box-inner.list-box-inner-first'),page_check)) 
                    time.sleep(5)
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
