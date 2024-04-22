from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tt_ttec_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tt_ttec_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'tt_ttec_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'TTD'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    
    # Onsite Field -Opening Date
    # Onsite Comment -None Monday 11th September, 2023

    try:
        publish_date1 = tender_html_element.find_element(By.CSS_SELECTOR, "td.sorting_1").text
        publish_date_day1 = re.findall('\d+\w{2}',publish_date1)[0]
        if 'th' in publish_date_day1:
            publish_date_day =publish_date_day1.replace('th','')
        elif 'nd'in publish_date_day1:
            publish_date_day =publish_date_day1.replace('sd','')
        elif 'st' in publish_date_day1:
            publish_date_day =publish_date_day1.replace('st','')
        publish_date_year = re.findall('\w+, \d{4}',publish_date1)[0]
        publish_date = publish_date_day+' '+publish_date_year
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None 30th November, 2023 TIME : 11:45am

    try:
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_deadline_day = re.findall('\d{2}',notice_deadline1)[0]
        notice_deadline_year = re.findall('\w+, \d{4}',notice_deadline1)[0]
        notice_deadline_time = re.findall('\d+:\d+',notice_deadline1)[0]
        notice_deadline = notice_deadline_day+' '+notice_deadline_year+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Number
    # Onsite Comment -Note:Take only numeric value

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > center').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details >> Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5) > table > tbody > tr:nth-child(2) > td:nth-child(1)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details >> Quantity
    # Onsite Comment -None

    try:
        tender_quantity = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(5) > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
        if 'N/A' in tender_quantity:
            notice_data.tender_quantity = ''
        else:
            notice_data.tender_quantity = tender_quantity
    except Exception as e:
        logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'TRINIDAD AND TOBAGO ELECTRICITY COMMISSION'
        customer_details_data.org_parent_id = '7562204'
        customer_details_data.org_country = 'TT'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
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
    urls = ["https://ttec.co.tt/default/procurement-supplies-tenders-public"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        iframe = page_main.find_element(By.XPATH,'//*[@id="av-layout-grid-1"]/div/div/section/div/p/iframe')
        page_main.switch_to.frame(iframe)
        time.sleep(3)

        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#example1 > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#example1 > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#example1 > tbody > tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#example1 > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break

        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
