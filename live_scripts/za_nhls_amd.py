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
from gec_common import functions as fn
import gec_common.Doc_Download_ingate as Doc_Download
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "za_nhls_amd"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'EN'
    notice_data.currency = 'ZAR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 16
    
    notice_data.procurement_method = 2
    notice_data.script_name = "za_nhls_amd"
    
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.ninja_column_2.ninja_clmn_nm_description').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    notice_data.notice_url = url
    
    try:
        if notice_data.notice_url == "https://www.nhls.ac.za/supply-chain/bid-cancellations-2/":
            notice_data.document_type_description = "Bid Cancellations"

        elif notice_data.notice_url == "https://www.nhls.ac.za/supply-chain/bid-withdrawalnew-look/":
            notice_data.document_type_description = "Bid Withdrawal"

        elif notice_data.notice_url == "https://www.nhls.ac.za/supply-chain/supply-chain-management-scm-procedures-policies/rfq-cancellations/":
            notice_data.document_type_description = "RFQ Cancellations"

        else:
            notice_data.document_type_description = "RFQ Withdrawal"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.ninja_column_0.ninja_clmn_nm_rfq_number.footable-first-visible').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, " td.ninja_column_3.ninja_clmn_nm_closing_date").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = "NATIONAL HEALTH LABORATORY SERVICE"
        
        org_parent_id ="7234267"
        customer_details_data.org_parent_id = int(org_parent_id)
        

        customer_details_data.org_city  = "1 Modderfontein Road,Sandringham,Johannesburg,South Africa"
        
        customer_details_data.org_phone  = '011-386-6000'
        
        customer_details_data.org_email  = 'enquiries@nhls.ac.za'
        
        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_deadline) +  str(notice_data.notice_url) 
    
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
    urls = ["https://www.nhls.ac.za/supply-chain/bid-cancellations-2/","https://www.nhls.ac.za/supply-chain/bid-withdrawalnew-look/","https://www.nhls.ac.za/supply-chain/supply-chain-management-scm-procedures-policies/rfq-cancellations/","https://www.nhls.ac.za/supply-chain/rfq-withdrawal-2/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#wptp-form > div > input.termsagree'))).click()
            time.sleep(5)
        except:
            pass
        
        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/main/div/section/div/div/div/table/tbody/tr'))).text
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/main/div/section/div/div/div/table/tbody/tr')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/main/div/section/div/div/div/table/tbody/tr')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
