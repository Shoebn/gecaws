
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "kw_kcb_ca"
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
SCRIPT_NAME = "kw_kcb_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'kw_kcb_ca'
    notice_data.main_language = 'AR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KW'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'KWD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    

    Name_of_the_award_company_text = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
    if Name_of_the_award_company_text== '':
        return
    
    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)

    notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text 

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text 
        notice_data.publish_date = datetime.strptime(publish_date, '%m/%d/%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass          

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return     

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    notice_data.notice_url = "https://www.kcb.gov.kw/sites/arabic/Pages/ApplicationPages/TendersAnnouncements.aspx" 

    try:
        document_fee = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text  
        if len(document_fee)>2:
            notice_data.document_fee = document_fee.split('دك')[0].strip()
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass 

    try:
        contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10)').text  
        if len(contract_duration)>2:
            notice_data.contract_duration = contract_duration
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass 

    try:              
        lot_details_data = lot_details()

        lot_details_data.lot_title = notice_data.notice_title
        lot_details_data.lot_number = 1

        try:
            bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(8)').text
            if len(bidder_name)>3:
                award_details_data = award_details()
                award_details_data.bidder_name = bidder_name
                grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(11)').text  
                if len(grossawardvaluelc)>2:
                    grossawardvaluelc = grossawardvaluelc.replace(',','')
                    try:
                        award_details_data.grossawardvaluelc = float(grossawardvaluelc.split('دك')[0].strip())
                    except:
                        award_details_data.grossawardvaluelc = float(grossawardvaluelc.split('د.ك')[0].strip())

                award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                if len(award_date)>2:
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date, '%m/%d/%Y').strftime('%Y/%m/%d')

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass    

    try:              
        customer_details_data = customer_details()
        try:
            customer_details_data.org_name = 'KUWAIT CREDIT BANK'
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        customer_details_data.org_parent_id = '7555639'
        customer_details_data.org_phone = '1810000'
        customer_details_data.org_country = 'KW'
        customer_details_data.org_language = 'AR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document' 
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(12) > a").get_attribute('href') 
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.kcb.gov.kw/sites/arabic/Pages/ApplicationPages/TendersAnnouncements.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
                
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr:nth-child(1)'))).text  
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))
                length = len(rows)
                for records in range(0,length-2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))[records] 
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
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'tbody > tr:nth-child(1)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'tbody > tr:nth-child(1)'),page_check)) 
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
    output_json_file.copyFinalJSONToServer(output_json_folder)