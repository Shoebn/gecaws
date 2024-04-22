from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_aegcl"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_aegcl"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_aegcl'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
   
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    # Onsite Field -Tender No
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Details
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Submission Start Date (DD-MM-YYYY HH:MM IST)
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4} \d{2}:\d{2}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Tender End Date (DD-MM-YYYY HH:MM IST)
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d{2}:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Opening Date (DD-MM-YYYY HH:MM IST)
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender No
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div > table > tbody > tr > td').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Work type
    # Onsite Comment -Relace following keywords with given keywords("Civil Works=Works","Civil & Electrical Work=Works","Supply=Supply")

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Work type")]//following::td').text
        if "Supply" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Civil Works" in notice_contract_type or "Electrical Construction Works" in notice_contract_type or "Civil & Electrical Work" in notice_contract_type or "Works" in notice_contract_type or "Technical Work" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Pre Bid Meeting Date
    # Onsite Comment -None

    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Pre Bid Meeting Date")]//following::td').text
        pre_bid_meeting_date = re.findall('\d+-\d+-\d{4} \d{2}:\d{2}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Inviting Authority >> Total tender value(excluding/including GST)
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Total tender value(excluding/including GST)")]//following::td').text
        est_amount = re.sub("[^\d+]","",est_amount)
        notice_data.est_amount =float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Inviting Authority >> Total tender value(excluding/including GST)
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Tender Inviting Authority
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = 'ASSAM ELECTRICITY GRID CORPORATION LTD'
        customer_details_data.org_parent_id = '7643684'
        
        # Onsite Field -Tender Inviting Authority >> Designation
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Designation")]//following::td').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Tender Inviting Authority >> Address
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::td').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td > strong > a'):
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
            attachments_data.file_name = "Documents"
        
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://apps.aegcl.co.in/tenders/tenderarchive?page="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tab_a"]/div/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tab_a"]/div/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tab_a"]/div/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                try: 
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="toplist"]/li/div'),page_check))
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
