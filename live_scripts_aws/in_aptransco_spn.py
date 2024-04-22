from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_aptransco_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "in_aptransco_spn"
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
    notice_data.script_name = 'in_aptransco_spn'
    
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
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -Tender Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Notification
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(1)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Tender Notification
#     # Onsite Comment -None

    try:
        notice_data.document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.document_purchase_start_time = re.findall('\d+-\d+-\d{4}',notice_data.document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(notice_data.document_purchase_start_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Expiry Date
#     # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Expiry Date
#     # Onsite Comment -None

    try:
        notice_data.document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.document_purchase_end_time = re.findall('\d+-\d+-\d{4}',notice_data.document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(notice_data.document_purchase_end_time,'%d-%m-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -None
    notice_data.notice_url = 'https://apps.aptransco.co.in/tenders/tender.aspx'
    
#     # Onsite Field -None
#     # Onsite Comment -None

    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:              
        customer_details_data = customer_details()

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name = 'TRANSMISSION CORPORATION OF ANDHRA PRADESH LIMITED'
        customer_details_data.org_parent_id = '7589575'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
# # Onsite Field -None
# # Onsite Comment -Note:Click on this "_lnkview_" than grab the data

    try: 
        no=1
        clk=tender_html_element.find_element(By.XPATH, f'(/html/body/div/form/div[3]/div/div/div[11]/div[2]/div/div[2]/div/div[3]/div/table/tbody/tr/td[5]/a)[{no}]').click()
        time.sleep(5)

        page_main.switch_to.window(page_main.window_handles[1])
        clk=page_main.find_element(By.CSS_SELECTOR, 'a#GVTenders_lnkview_0').click()
        time.sleep(10)

        attachments_data = attachments()
        attachments_data.file_name =page_main.find_element(By.CSS_SELECTOR, 'a#GVTenders_lnkview_0').text
        page_main.switch_to.window(page_main.window_handles[2])

        attachments_data.external_url=page_main.current_url
        time.sleep(10)
        attachments_data.file_type = attachments_data.external_url.split('.')[-1]

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)

        page_main.close()
        page_main.switch_to.window(page_main.window_handles[0])
        time.sleep(5)
        no += 1
    except:
        pass
        

# # Onsite Field -None
# # Onsite Comment -None
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_title) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized','--disable-popup-blocking']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://apps.aptransco.co.in/tenders/tender.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="Content_GVTenders"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Content_GVTenders"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Content_GVTenders"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 30).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="Content_GVTenders"]/tbody/tr'),page_check))
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
