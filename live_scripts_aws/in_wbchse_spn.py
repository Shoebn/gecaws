from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_wbchse_spn"
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
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_wbchse_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_wbchse_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
    notice_data.document_type_description = "TENDER-NIT"
    
    
    try:  
        notice_deadline =  tender_html_element.find_element(By.CSS_SELECTOR,'div.jet-listing-dynamic-field__content').text.split("Close Date:")[1].strip()
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
 
    
    try:  
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'div.elementor-element.elementor-element-1e6ae02.elementor-widget__width-auto.ob-harakiri-inherit.ob-has-background-overlay.elementor-widget.elementor-widget-heading > div > p').text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
      
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.elementor-element.elementor-element-d823453.ob-harakiri-inherit.ob-has-background-overlay.elementor-widget.elementor-widget-heading > div > p').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details() 
        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'div.elementor-element.elementor-element-d96821d.elementor-widget__width-auto.jedv-enabled--yes.ob-harakiri-inherit.ob-has-background-overlay.elementor-widget.elementor-widget-heading > div > p').text.split("From:")[1].strip()
        except:
            pass
        customer_details_data.org_name = 'WEST BENGAL COUNCIL OF HIGHER SECONDARY EDUCATION'
        customer_details_data.org_parent_id = 7726595
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
 
    try: 
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.elementor-button.elementor-size-md.jet-download.jet-download-icon-position-left').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments_data: {}".format(type(e).__name__))
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
    urls = ["https://wbchse.wb.gov.in/notices/?jsf=jet-engine:notices-grid&tax=type-of-notice:12"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/section[2]/div/div/div[2]/div/div/div[1]/div/div/div/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/section[2]/div/div/div[2]/div/div/div[1]/div/div/div/div')))
                length = len(rows)                                                                              
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/section[2]/div/div/div[2]/div/div/div[1]/div/div/div/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[2]/div/section[2]/div/div/div[2]/div/div/div[2]/div/div/div/div[7]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[2]/div/section[2]/div/div/div[2]/div/div/div[1]/div/div/div/div'))).text
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[2]/div/section[2]/div/div/div[2]/div/div/div[1]/div/div/div/div'),page_check))
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
