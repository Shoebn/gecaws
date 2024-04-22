from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_nhsrcl_spn"
log_config.log(SCRIPT_NAME)
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
SCRIPT_NAME = "in_nhsrcl_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_nhsrcl_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.XPATH, '/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']/td[3]/p[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.XPATH,'/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']/td[2]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.find_element(By.XPATH,'/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']').get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.XPATH, '/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']/td[4]').text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = tender_html_element.find_element(By.XPATH,'/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']/td[5]').text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+ [AMPMampm]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "NATIONAL HIGH SPEED RAIL CORPORATION LIMITED"
        customer_details_data.org_parent_id = 7558197
        customer_details_data.org_address = "National High Speed Rail Corporation Limited (NHSRCL) 2nd FLOOR, ASIA BHAWAN, ROAD NO-205 SEC-09, DWARKA, New Delhi -110077"
        customer_details_data.org_phone = '011-28070000/01/02/03/04'
        customer_details_data.org_fax = '011-28070150'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try: 
        attachments_click = tender_html_element.find_element(By.XPATH,'/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']/td[6]').click()
        time.sleep(3)
    except:
        pass
        
    tender_no += 1
    try:                                                           
        for single_record in tender_html_element.find_elements(By.XPATH,'/html/body/div[2]/div/div/div[3]/div/main/section/div/div[2]/div/div/div/div[2]/table/tbody/tr['+str(tender_no)+']/td/div/div/div/table/tbody/tr'):
            try:
                notice_data.notice_text += single_record.get_attribute('outerHTML')
            except:
                pass
                
            for single_record1 in single_record.find_elements(By.CSS_SELECTOR,'td:nth-child(2) > span > a'):
                attachments_data = attachments()
                attachments_data.external_url = single_record1.get_attribute('href')
                print('attachments_data.external_url',attachments_data.external_url)
                attachments_data.file_name = single_record1.text
                print('attachments_data.file_name',attachments_data.file_name)
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
    logging.info(notice_data.identifier)
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
    urls = ["https://www.nhsrcl.in/tenders/active-tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#block-nhsrcl-content > div > div > div > div.view-content > table > tbody > tr')))
            length = len(rows)
            tender_no = 1
            for records in range(0,length-2):
                tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#block-nhsrcl-content > div > div > div > div.view-content > table > tbody > tr')))[records]
                print(tender_html_element.text)
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