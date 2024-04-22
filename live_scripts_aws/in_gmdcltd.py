from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_gmdcltd"
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
SCRIPT_NAME = "in_gmdcltd"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_gmdcltd'

    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2

    notice_data.currency = 'INR'

    notice_data.document_type_description = 'Current Tenders'
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > p:nth-child(2)').text
        if 'RFP No.' in notice_no:
            notice_data.notice_no = notice_no.split('RFP No.')[1].strip()
        elif 'EOI No.' in notice_no:
            notice_data.notice_no = notice_no.split('EOI No.')[1].strip()
        elif 'e-Auction No.' in notice_no:
            notice_data.notice_no = notice_no.split('e-Auction No.')[1].strip()
        else:
            notice_data.notice_no = notice_no
        
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > p:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    pre_bid_meeting_date1 = tender_html_element.find_element(By.XPATH, 'div').text    
    if 'Pre Bid Meeting :' in pre_bid_meeting_date1:
        
        try:      
            pre_bid_meeting_date2 = pre_bid_meeting_date1.split('Pre Bid Meeting :')[1].split('\n')[1].split('\n')[0].strip()
            try:  
                pre_bid_meeting_date = re.findall('\d+\w+ \w+ \d{4}',pre_bid_meeting_date2)[0]
                notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%dth %B %Y').strftime('%Y/%m/%d')
            except:
                pre_bid_meeting_date = re.findall('\d+-\d+-\d{4}',pre_bid_meeting_date2)[0]
                notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%m-%Y').strftime('%Y/%m/%d')
        except:
            pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div > p:nth-child(6)").text
        if 'at' in notice_deadline:
            try:
                notice_deadline = notice_deadline.split('at')[0].strip()
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%dth %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = notice_deadline.split('at')[0].strip()
                notice_data.notice_deadline  = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        else:
            try:
                notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')  
        logging.info(notice_data.notice_deadline)

    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is None:
        return

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    notice_data.notice_url = 'https://www.gmdcltd.com/current-tenders/'
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div.row > div.tender-section').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Gujarat Mineral Development Corporation Ltd'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_parent_id = '7538634'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.box-shadow-common '):
            attachments_data = attachments()

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.report-margin-zero').text  
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_type = tender_html_element.find_element(By.XPATH, 'div').text     
    
    if 'Corrigendum' in notice_type or 'Notification of Extension' in notice_type or 'Amendment' in notice_type :
        notice_data.notice_type = 16
        
    elif 'EOI' in notice_type:
        notice_data.notice_type = 5
    else:
        notice_data.notice_type = 4

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
    urls = ["https://www.gmdcltd.com/en/current-tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div[3]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div[3]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
