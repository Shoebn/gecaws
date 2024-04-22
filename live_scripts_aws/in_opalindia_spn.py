from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_opalindia_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_opalindia_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'in_opalindia_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'INR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -1.take only number.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text.split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Tender description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender sale period
    # Onsite Comment -1.here "02.11.2023 09:00 Hrs to 23.11.2023 14:00 Hrs" take first date as publish_date

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(6)").text.split('to')[0]
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Tender sale period
#     # Onsite Comment -1.here "02.11.2023 09:00 Hrs to 23.11.2023 14:00 Hrs" take first date as document_purchase_end_time

    try:
        notice_data.document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(6)').text.split('to')[0]
        notice_data.document_purchase_start_time = re.findall('\d+.\d+.\d{4}',notice_data.document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(notice_data.document_purchase_start_time,'%d.%m.%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Tender sale period
#     # Onsite Comment -1.here "02.11.2023 09:00 Hrs to 23.11.2023 14:00 Hrs" take second date as document_purchase_end_time

    try:
        notice_data.document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(6)').text.split('to')[1]
        notice_data.document_purchase_end_time = re.findall('\d+.\d+.\d{4}',notice_data.document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(notice_data.document_purchase_end_time,'%d.%m.%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Closing date and time for Bid / EOI, Techno Commercial Bid Submission
#     # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(9)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


#     # Onsite Field -Date & Time for opening of prequalification/ techno commercial bid
#     # Onsite Comment -

    try:
        notice_data.document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(10)').text
        notice_data.document_opening_time  = re.findall('\d+-\d+-\d{4}',notice_data.document_opening_time )[0]
        notice_data.document_opening_time  = datetime.strptime(notice_data.document_opening_time ,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'td > table > tbody > tr > td.inllinetab > table > tbody > tr  '):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_name = 'ONGC PETRO ADDITIONS LIMITED'
            customer_details_data.org_parent_id = '7533412'
        # Onsite Field -Contact Details:
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass


        # Onsite Field -Contact Details:
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass


        # Onsite Field -Contact Details:
        # Onsite Comment -None

            try:
                customer_details_data.org_email = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass


            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'tr > td:nth-child(11)'):
            attachments_data = attachments()
        # Onsite Field -Links for Downloading Tender Documents
        # Onsite Comment -1.take in text format

            attachments_data.file_name ='Tender Document'

        # Onsite Field -Links for Downloading Tender Documents
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

        # Onsite Field -Links for Downloading Tender Documents
        # Onsite Comment -1.split file_type


            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
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
    urls = ["https://www.opalindia.in/tenders.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tender > table > tbody:nth-child(n) '))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tender > table > tbody:nth-child(n) ')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tender > table > tbody:nth-child(n) ')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tender > table > tbody:nth-child(n) '),page_check))
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
