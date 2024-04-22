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
SCRIPT_NAME = "in_meconlimited_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tender_no
    notice_data = tender()
    
    notice_data.script_name = 'in_meconlimited_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'INR'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(7)').text
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+ [AMPMampm]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        if 'Amendment' in notice_type or 'Corrigendum' in notice_type:
            notice_data.notice_type = 16
            try:
                notice_deadline = re.findall('\d+.\d+.\d{2}',notice_type)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass
        else:
            notice_data.notice_type = 4
    except:
        pass

    try:
        document_purchase_end_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        document_purchase_end_time = re.findall('\d+-\w+-\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "MECON LIMITED"
        customer_details_data.org_parent_id = 7522250
        customer_details_data.org_address = "MECON Limited, Vivekananda Path, P.O.Doranda, Ranchi, Jharkhand"
        customer_details_data.postal_code = '834002'
        customer_details_data.postal_fax = '0651-2482189 /2214'
        customer_details_data.org_phone = '0651-2483000'
        customer_details_data.org_email = 'ranchi@meconlimited.co.in'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
    urls = ["http://www.meconlimited.co.in/active_tender.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,4):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/div[4]/div/div[2]/div[7]/div[3]/div/div[2]/div/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[4]/div/div[2]/div[7]/div[3]/div/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length-2):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/div[4]/div/div[2]/div[7]/div[3]/div/div[2]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/div[4]/div/div[2]/div[7]/div[3]/div/div[2]/div/table/tbody/tr[2]'),page_check))
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