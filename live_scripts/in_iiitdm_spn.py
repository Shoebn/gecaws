from gec_common.gecclass import *
import logging
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
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tender_no = 0
SCRIPT_NAME = "in_iiitdm_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_iiitdm_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h1').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p:nth-child(1)').text.split('Tender No:')[1].strip()
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try: 
        published_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > p:nth-child(2)").text
        try:
            p_date = re.findall(r'\d+[a-z]+',published_date)[0]
            p_date1 = published_date.split(p_date)[1].strip()
            if 'th' in p_date or 'nd' in p_date or 'rd' in p_date or 'st' in p_date:
                publish_date1 = p_date.replace('th','').replace('nd','').replace('rd','').replace('st','').strip()
                publishing_date = publish_date1 + ' ' + p_date1
        except:
            pass
        try:
            publish_date = re.findall('\d+-\d+-\d{4}',published_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish_date = re.findall('\d+/\d+/\d{4}',published_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                try:
                    publish_date = re.findall('\d+.\d+.\d{4}',published_date)[0]
                    notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')  
                except:
                    try: 
                        publish_date = re.findall('\d+ \w+ \d{4}',publishing_date)[0]
                        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')   
                    except:
                        try:
                            publish_date = re.findall('\d+ \w+, \d{4}',publishing_date)[0]
                            notice_data.publish_date = datetime.strptime(publish_date,'%d %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            publish_date = re.findall('\d+ \w+, \d{4}',publishing_date)[0]
                            notice_data.publish_date = datetime.strptime(publish_date,'%d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
                            
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, 'div > p:nth-child(3)').text.split('Last Date:')[1].strip()
        check_lst = ['st', 'nd', 'rd', 'th']
        for i in check_lst:
            notice_deadline = notice_deadline.replace(i, '').replace(',', '').replace(';', '').replace('at', '').replace('-', '')

        try: #15.06.2022-15 00 Hrs
            notice_deadline1 = re.findall(r'\d+ [\w.]+ \d{4}', notice_deadline)[0]
            timing = re.findall(r'\d{2}:\d{2}', notice_deadline)[0] if "PM" not in notice_deadline and "AM" not in notice_deadline else re.findall(r'\d+.\d+.[A-Za-z][a-zA-Z]', notice_deadline)[0]
            date_time_data = notice_deadline1 + ' ' + timing
            formats = ['%d %B %Y %I.%M %p', '%d %B %Y %I:%M%p', '%d %B %Y %H:%M', '%d.%m.%Y %I.%M %p','%d.%m.%Y-%H %M', '%d-%m-%Y %I.%M %p']
            for fmt in formats:
                try:
                    notice_data.notice_deadline = datetime.strptime(date_time_data, fmt).strftime('%Y/%m/%d %H:%M:%S')
                    break
                except:
                    pass
        except:
            pass
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        pre_bid_meeting_date = tender_html_element.find_element(By.CSS_SELECTOR,'div > p:nth-child(5)').text
        if 'th' in pre_bid_meeting_date or 'nd' in pre_bid_meeting_date or 'st' in pre_bid_meeting_date or 'rd' in pre_bid_meeting_date:
            meeting_date = pre_bid_meeting_date.replace('th','').replace('rd','').replace('nd','').replace('st','').replace(',','').strip()
            pre_bid_meeting_date = re.findall('\d+ \w+ \d{4}',meeting_date)[0]
            notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d %B %Y').strftime('%Y/%m/%d')
        else: 
            meeting_date = re.findall('\d+.\d+.\d{4}',pre_bid_meeting_date)[0]
            notice_data.pre_bid_meeting_date = datetime.strptime(meeting_date,'%d.%m.%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
        

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "INDIAN INSTITUTE OF INFORMATION TECHNOLOGY DESIGN AND MANUFACTURING (IIITD&M)"
        customer_details_data.org_parent_id = 7533413
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:  
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,'div  a'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.file_name = 'Tender Document'
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass
    
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tender_no += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.iiitdm.ac.in/tender-notice"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div > div.overflow-hidden > main > ul > li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div > div.overflow-hidden > main > ul > li')))[records]
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