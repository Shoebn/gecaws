
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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_sppprajast_spn"
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
    notice_data.script_name = 'in_rajasthan'
    
    # Onsite Field -some records are published in "HINDI" also
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'INR'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = single_record.find_element(By.XPATH, '//*[contains(text(),'NIB Reference no')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.est_amount = single_record.find_element(By.XPATH, '//*[contains(text(),'Bid Amount')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = single_record.find_element(By.XPATH, '//*[contains(text(),'Bid Amount')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_contract_type = single_record.find_element(By.XPATH, '//*[contains(text(),'Bid Type')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Title')]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Title')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Title')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Pattern')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#print-this-table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#print-this-table > tbody'):
            customer_details_data = customer_details()
        # Onsite Field -also take "//*[contains(text(),'Department Type')]//following::td[1]" take this selector too in org_name  and split both the data by "comma" ","
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Department Name')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = single_record.find_element(By.XPATH, '//*[contains(text(),'Procuring Entity Name:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_address = single_record.find_element(By.XPATH, '//*[contains(text(),'Office Address:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split "Fax No. :" from the data
        # Onsite Comment -None

            try:
                customer_details_data.org_fax = single_record.find_element(By.XPATH, '//*[contains(text(),'Office Address:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_email = single_record.find_element(By.XPATH, '//*[contains(text(),'Entity Contact')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -split "Phone No." from data
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = single_record.find_element(By.XPATH, '//*[contains(text(),'Office Address:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
        # Onsite Field -split data for "Pin"
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = single_record.find_element(By.XPATH, '//*[contains(text(),'Office Address:')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#print-this-table > tbody'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Title')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Title')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.XPATH, '//*[contains(text(),'Required in Cover')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = single_record.find_element(By.XPATH, '//*[contains(text(),'Bid Amount')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.contract_type = single_record.find_element(By.XPATH, '//*[contains(text(),'Bid Type')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#print-this-table > tbody'):
            attachments_data = attachments()
            # Onsite Field -None
            # Onsite Comment -None
            
            external_url = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Document')]//following::td[1]').click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
        
        # Onsite Field -split size from the data
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Document')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Document')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Bid Document')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://sppp.rajasthan.gov.in/bidlist.php"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/form/table/tbody/tr[5]/td/div/div[2]/div/table/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    