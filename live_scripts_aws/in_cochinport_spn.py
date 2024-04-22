from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_cochinport_spn"
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
SCRIPT_NAME = "in_cochinport_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_cochinport_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.procurement_method = 2
    notice_data.document_type_description = 'Tender'
    
    # Onsite Field -Tender Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-tender-number').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Document Issue from Date
    # Onsite Comment -None

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-document-issue-date').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Document Issue to Date
    # Onsite Comment -None

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-document-issue-to-date').text
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-document-issue-date').text
        publish_date = re.findall('\d+/\d+/\d{4}, -\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y, -%H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Last Date of Submission
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.views-field.views-field-field-last-date-of-submission").text
        notice_deadline = re.findall('\d+/\d+/\d{4}, -\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y, -%H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Open Date
    # Onsite Comment -None

    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-tender-open-date').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment -None
#     notice_data.publish_date = 'take publish_date as a threshold date'
    
    # Onsite Field -EMD
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-earnest-money-deposit-emd-').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Description
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    # Onsite Field -Tender Value
    # Onsite Comment -None

    try:
        est_amountt = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(9) div.field__item').text.split('Rs.')[1].strip()
        if 'lakhs' in est_amountt:
            est_amount = re.sub("[^\d\.\,]", "",est_amountt)
            est_amountttttt = float(est_amount)*100000
            notice_data.est_amount = est_amountttttt
            notice_data.grossbudgetlc = notice_data.est_amount
        else:
            est_amount = re.sub("[^\d\.\,]", "",est_amountt)
            est_amount = est_amount.replace(',','').strip()
            notice_data.est_amount = float(est_amount)
            notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#block-gavias-tico-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    
    # Onsite Field -Cost of Tender Document including taxes
    # Onsite Comment -None

    try:
        doct_cost = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(11) div.field__item').text.split('Rs.')[1].split('(')[0].strip()
        document_cost = re.sub("[^\d]", "",doct_cost)
        if ',' in document_cost:
            document_cost = document_cost.replace(',','').strip()
            notice_data.document_cost = float(document_cost)
        else:
            notice_data.document_cost = float(document_cost)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
# Onsite Field -Contact Details
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Cochin Port'
        customer_details_data.org_parent_id = '7783663'
    # Onsite Field -Contact Details >> Contact Person Name and Designation
    # Onsite Comment -split only contact_person for ex."Smt. Siny Mathew, Supdtg. Engineer (Tech.)" , here take only "Smt. Siny Mathew"    , ref_url : "https://www.cochinport.gov.in/capital-dredging-manoeuvring-basin-indian-navy-north-jetty-naval-base-kochi"

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(22) div.field__item').text.split(',')[0].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Details >> Contact Address
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(23) div.field__item').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact Details >> Contact Address
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(24) div.field__item').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Tender Notice
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#block-gavias-tico-content  div:nth-child(25) > div > div.field__items  span > a'):
            attachments_data = attachments()
        # Onsite Field -Tender Notice
        # Onsite Comment -take only text format

            attachments_data.file_name = single_record.text
            if 'Addendum' in attachments_data.file_name or 'Corrigendum' in attachments_data.file_name or 'amendments' in attachments_data.file_name or 'Extension of' in attachments_data.file_name:
                notice_data.notice_type = 16
            elif "EXPRESSION OF INTEREST" in attachments_data.file_name or 'EOI' in attachments_data.file_name:
                notice_data.notice_type = 5
            else:
                notice_data.notice_type = 4
        # Onsite Field -Tender Notice
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.cochinport.gov.in/tender"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-views-block-announcements-block-3"]/div/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-views-block-announcements-block-3"]/div/div/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
