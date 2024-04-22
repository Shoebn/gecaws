from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_hal_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_hal_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_hal_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'INR'
        
    notice_data.notice_type = 4
    
    notice_data.notice_url = url
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass 
    
    try:
        address1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        address2 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        address = address1+','+address2
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_name =  "HINDUSTAN AERONAUTICS LIMITED"
        customer_details_data.org_parent_id = 7538882   
        customer_details_data.org_address = 'HINDUSTAN AERONAUTICS LIMITED Accessories Division,Lucknow Post Office,Lucknow - 226 016 Uttar Pradesh, India'+','+address
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass 
    
    try:
        page_details_click = WebDriverWait(tender_html_element, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(2) > a > u")))
        page_main.execute_script("arguments[0].click();",page_details_click)
        time.sleep(5)
        WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#primary > div')))

        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#primary > div').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

        try:         
            attachment = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Documents / Details")]//following::td[1]').text
            if 'Click here to View' in attachment:
                notice_url1  = page_main.find_element(By.CSS_SELECTOR, '#primary > div > div.carreers-deatils-page > div > div.card-body > div > table > tbody > tr:nth-child(5) > td:nth-child(2) > div > span > a').get_attribute("href")

                fn.load_page(page_details,notice_url1,60)
                logging.info(notice_url1)

                try:
                    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.panel > div.bpanel.p_false').get_attribute("outerHTML")                     
                except:
                    pass

                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.panel > div.bpanel.p_false > form > div.summary > table > tbody > tr')[1:]:
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) >ul >li >  a').get_attribute("href")

                    try:
                        attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                    except:
                        pass

                    if attachments_data.file_name != '--':
                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)

            else:   
                for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"Tender Documents / Details")]//following::td[1]/div/span/a'):
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.text

                    attachments_data.external_url = single_record.get_attribute("href")

                    try:
                        attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                    except:
                        pass

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        
    page_main.execute_script("window.history.go(-1)")
    time.sleep(5)
    WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#primary > div > div.tender-deatils > table > tbody > tr')))
         
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://hal-india.co.in/tender"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)  
          
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#primary > div > div.tender-deatils > table > tbody > tr:nth-child(3)'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#primary > div > div.tender-deatils > table > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#primary > div > div.tender-deatils > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="primary"]/div/div[5]/pagination-controls/pagination-template/nav/ul/li[10]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#primary > div > div.tender-deatils > table > tbody > tr:nth-child(3)'),page_check))
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
