from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_nato_spn"
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
import gec_common.Doc_Download
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "mfa_nato_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'mfa_nato_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'US'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'USD'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,100)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split('\n')[1].strip()
        notice_data.notice_title =GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b %Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)  
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split('\n')[1].strip()
        if 'Supply' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif 'Service' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text.split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'NATO SUPPORT AND PROCUREMENT AGENCY'
        customer_details_data.org_parent_id = 7778447
        customer_details_data.org_address = 'NSPA L-8302 CAPELLEN(Luxembourg)'
        customer_details_data.org_phone = 'TEL:(+352)3063(+ext.)'
        customer_details_data.org_fax = '(+352)3063 4300'

        try:
            org_address = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
            customer_details_data.org_address = customer_details_data.org_address + ',' + org_address
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
            
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH,'//*[contains(text(),"Buyer Email Address")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
            
        customer_details_data.org_country = 'US'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#Attachments > div > div.col-xs-12.col-lg-6 > div > div > div > div > div > div > ul >li > small'):
            attachments_data = attachments()
    
            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a")))
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
        
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'a > span:nth-child(2)').text
    
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR,'a > span:nth-child(3)').text.split('(')[1].split(')')[0].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__)) 
                pass
           
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR,'a > span').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__)) 
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://eportal.nspa.nato.int/eProcurement/RFP/PublicRFPList.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table.table.table-hover.table-condensed > tbody > tr'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-hover.table-condensed > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table.table-hover.table-condensed > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(3)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ContentPlaceHolder1_Scontent_DataList1 > tbody > tr > td'),page_check))
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
