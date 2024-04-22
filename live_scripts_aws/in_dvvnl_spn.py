from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_dvvnl_spn"
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
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_dvvnl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_dvvnl_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'AMEMDED' in notice_type:
            notice_data.notice_type = 16
    except:
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        url_id = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
        notice_data.notice_url = 'https://www.dvvnl.org/TenderInfo.aspx?id='+str(url_id)                 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ContentPlaceHolder1_UpdatePanel1').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        publish_date = page_details.find_element(By.XPATH,'//*[contains(text(),"Publish Date")]//following::td[2]').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> Closing

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '''//*[contains(text(),"Close Date of Tender")]//following::td[2]''').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Category")]//following::td[2]').text
        if 'Supply of Material' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Work contract' in notice_data.contract_type_actual or 'Civil Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '''//*[contains(text(),"EMD")]//following::td[2]''').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '''//*[contains(text(),"Tender Fees")]//following::td[2]''').text 
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Open Date of Tender")]//following::td[2]''').text
        tender_contract_start_date = re.findall('\d+/\d+/\d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass
    
    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '''//*[contains(text(),"Close Date of Tender")]//following::td[2]''').text
        tender_contract_end_date = re.findall('\d+/\d+/\d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = "Dakshinanchal Vidyut Vitran Nigam Ltd"
        customer_details_data.org_parent_id = 7522110
        customer_details_data.org_email = "dvvnlmd@gmail.com"
        customer_details_data.org_fax = '(0562) 2605465'
        customer_details_data.org_phone = '1912, 1800-180-3023'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        attachments_data = attachments()
        # Onsite Field -RFP Document
        attachments_data.file_name = "Tender Document"
        # Onsite Field -RFP Document
        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Document")]//following::td[2]/a').get_attribute('href')
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.dvvnl.org/Tenders.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ContentPlaceHolder1_grdTenders > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_grdTenders > tbody > tr')))
                length = len(rows)
                for records in range(1,length-1):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ContentPlaceHolder1_grdTenders > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ContentPlaceHolder1_grdTenders > tbody > tr.gridViewPager > td > table > tbody > tr > td > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ContentPlaceHolder1_grdTenders > tbody > tr:nth-child(2)'),page_check))
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
