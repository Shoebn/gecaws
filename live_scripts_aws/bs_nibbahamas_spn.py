from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bs_nibbahamas_spn"
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
SCRIPT_NAME = "bs_nibbahamas_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'bs_nibbahamas_spn'

    notice_data.main_language = 'EN'

    notice_data.currency = 'BSD'

    notice_data.procurement_method = 2

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BS'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -If we get title as Request For Expressions of Interest then take notice type - 5
    
    # Onsite Field -None
    # Onsite Comment -None
    
    notice_data.notice_url = url
    
    notice_data.notice_type = 4
    
    # Onsite Field -Submission Deadline
    # Onsite Comment -also do grab date and time

    try:   
        deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text 
        try:
            deadline_date = re.findall('\w+ \d+[th,st,nd]+, \d{4}',deadline)[0]
            if 'a.m.' in deadline or 'p.m.' in deadline:
                deadline_time = re.findall('\d+:\d+ \w+.\w+',deadline)[0].replace('.','')
                notice_deadline = deadline_date +' '+ deadline_time
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %dth, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            else:
                deadline_time = re.findall('\d+:\d+ \w+',deadline)[0]
                notice_deadline = deadline_date +' '+ deadline_time
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %dst, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except:
            try:
                deadline_date = re.findall('\w+ \d+, \d{4}',deadline)[0]
                if 'a.m' in deadline or 'p.m' in deadline:
                    deadline_time = re.findall('\d+:\d+ \w+.\w+',deadline)[0].replace('.','')
                elif 'Noon' in deadline:
                    deadline_time = re.findall('\d+:\d+ \w+',deadline)[0].replace('.','')
                else:
                    deadline_time = re.findall('\d+:\d+ \w+',deadline)[0]
                notice_deadline = deadline_date +' '+ deadline_time
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except:
                try:
                    notice_deadline = re.findall('\w+ \d+, \d{4}',deadline)[0]
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                    logging.info(notice_data.notice_deadline)
                except Exception as e:
                    logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                    pass
    except:
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    if notice_data.notice_deadline is None:
        return
    # Onsite Field -Tender Proposal
    # Onsite Comment -If we get title as Request For Expressions of Interest then take notice type - 5

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if 'Request for Expressions of Interest' in notice_data.notice_title:
            notice_data.notice_type = 5
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, '#content-holder table:nth-child(9) > tbody > tr').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_name = 'National Insurance Board (NIB)'
        customer_details_data.org_parent_id = '7785812'
        customer_details_data.org_country = 'BS'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
    # Onsite Field -Tender Proposal
    # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute('href')
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').text
        
    # Onsite Field -Tender Proposal
    # Onsite Comment -None

        try:
            attachments_data.file_type = 'pdf'
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://www.nib-bahamas.com/_m1876/public-tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content-holder"]/div/div[1]/div/div/table[2]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-holder"]/div/div[1]/div/div/table[2]/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-holder"]/div/div[1]/div/div/table[2]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break
    
            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="content-holder"]/div/div[1]/div/div/table[2]/tbody/tr'),page_check))
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
    
