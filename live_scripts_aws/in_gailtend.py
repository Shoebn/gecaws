from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_gailtend"
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
import gec_common.functions as fn
from functions import ET
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

#Note:click on all active tender to get the tender data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_gailtend"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -click on all active tender to get the tender data
    notice_data.script_name = 'in_gailtend'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'
   
    notice_data.procurement_method = 2
    
   
    
    # Onsite Field -Ref. No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Subject
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -None
    # Onsite Comment -If local_title have keyword like 'Corrigendum Available' then notice type will be 16
    
    if 'Corrigendum' in notice_data.local_title:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4    
     #Onsite Field -Closing Date
    # Onsite Comment -Grab time also

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+:\d+ [apAP][mM]',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
     # Onsite Field -Tender Subject
    # Onsite Comment -Click on hyperlink
    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.textbox2link')))
        page_main.execute_script("arguments[0].click();",notice_url)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Tender Publication Date
    # Onsite Comment -Grab time also

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Tender Publication Date')]//following::td[1]").text
        publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+:\d+ [apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Tender Opening Date
    # Onsite Comment -Grab time also

    try:
        document_purchase_start_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Opening Date")]//following::td[1]').text
        document_purchase_start_time = re.findall('\w+ \d+, \d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Closing Date
    # Onsite Comment -Grab time also

    try:
        document_purchase_end_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Closing Date")]//following::td[1]').text
        document_purchase_end_time = re.findall('\w+ \d+, \d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Pre-Bid Meeting Date / Pre-Tender Meeting Date
    # Onsite Comment -Grab time also

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Pre-Bid Meeting Date / Pre-Tender Meeting Date ")]//following::td[1]').text
        pre_bid_meeting_date = re.findall('\w+ \d+, \d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%B %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
   
    
    # Onsite Field -None
    # Onsite Comment -Take all the data from page_detail as well the "tender_html_element" of each record
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(4)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Tender Category
    # Onsite Comment -notice contrac type mapping as per below("	Services=Service","Goods=Supply")

    try:
        notice_contract_type = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Category")]//following::td').text
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        if 'Goods' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tender Category
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Category")]//following::td').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass    
    
# Onsite Field -Tender Document
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'a.heading1'):
            attachments_data = attachments()
        # Onsite Field -Tender Document
        # Onsite Comment -Take a hyperlink......Don't take a file extention

            attachments_data.file_name = single_record.text
        # Onsite Field -Tender Document
        # Onsite Comment -Take only file extention
            attachments_data.external_url = single_record.get_attribute('href')
            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Document
        # Onsite Comment -note:For Notice type 4 take all attachment from "Tender Document :	"for notice type 16 take all attachment from "Corrigendum Details :." also
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


    try:              
        customer_details_data = customer_details()
    # Onsite Field -Tender Receiving Location
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Receiving Location")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = 'Gas Authority of India Limited (Gail)'
        customer_details_data.org_parent_id = '7533534'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        back = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Back')))
        page_main.execute_script("arguments[0].click();",back)
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://gailtenders.in/Gailtenders/Home.asp"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        close_button = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.btn-close')))
        page_main.execute_script("arguments[0].click();",close_button)
        
        all_active_tender = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'All Active Tenders')))
        page_main.execute_script("arguments[0].click();",all_active_tender)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr[22]/td/table/tbody/tr/td[7]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr[2]'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table/tbody/tr/td/table[2]/tbody/tr/td/table/tbody/tr'),page_check))
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
