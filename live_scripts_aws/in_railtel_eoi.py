from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_railtel_eoi"
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
SCRIPT_NAME = "in_railtel_eoi"
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_railtel_eoi'
    
    notice_data.currency = 'INR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.procurement_method = 2
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 5
    
    notice_data.document_type_description = "Active Expression of Interest"
    
#  notice_type : 5  , if in detail_page following field "Tender Corrigendum" has documents available then take notice_type = 16
      
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        try:
            publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[-1]
            notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                publish_date = re.findall('\d+ \d+ \d{4}',publish_date)[-1]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %m %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\d+[a-z]+ \w+ \d{4}',publish_date)[-1]
                if 'th'in publish_date or 'nd' in publish_date or 'st' in publish_date:
                    publish_date1 = (publish_date.replace('th','').replace('st','').replace('nd','')).strip()
                    notice_data.publish_date = datetime.strptime(publish_date1,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        try:
            document_opening_time = re.findall('\d+.\d+.\d{4}',document_opening_time)[-1]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
        except:
            try:
                document_opening_time = re.findall('\d+ \d+ \d{4}',document_opening_time)[-1]
                notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d %m %Y').strftime('%Y-%m-%d')
            except:
                document_opening_time = re.findall('\d+[a-z]+ \w+ \d{4}',document_opening_time)[-1]
                if 'th'in document_opening_time or 'nd' in document_opening_time or 'st' in document_opening_time:
                    document_opening_time1 = (document_opening_time.replace('th','').replace('st','').replace('nd','')).strip()
                    notice_data.document_opening_time = datetime.strptime(document_opening_time1,'%d %b %Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

#we can't grab notice no filed from site because patten is varry.
    
#     try:
#         notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
#     except Exception as e:
#         logging.info("Exception in notice_no: {}".format(type(e).__name__))
#         pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href") 
    except:
        pass
    
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div').get_attribute("outerHTML")                     
        except:
            pass
        
        try:              
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"File Link")]//following::td[1]/a'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text
                
                attachments_data.external_url = single_record.get_attribute('href')                

                if attachments_data.external_url != None:
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
            pass
        
        try:              
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Documents")]//following::td[1]/a'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text
                
                attachments_data.external_url = single_record.get_attribute('href')
                
                if attachments_data.external_url != None:
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
            pass
        
        try:              
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Corrigendum")]//following::td[1]/a'):
                attachments_data = attachments()
                notice_data.notice_type = 16

                attachments_data.file_name = single_record.text
                
                attachments_data.external_url = single_record.get_attribute('href')

                if attachments_data.external_url != None:
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_3: {}".format(type(e).__name__)) 
            pass
    
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = "RAILTEL"
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_parent_id= 7527849
            customer_details_data.org_city= "Delhi"
            customer_details_data.org_website = "www.railtelindia.com"
            customer_details_data.org_phone = "+91 11 22900600"
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["https://www.railtel.in/tenders/expression-of-interest.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:      
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > div > div.wrapper > div > div.tender_div > table > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div > div.wrapper > div > div.tender_div > table > tbody > tr')))
                length = len(rows)                                                                              
                for records in range(1,length):                                                                       
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > div > div.wrapper > div > div.tender_div > table > tbody > tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > div > div.wrapper > div > div.tender_div > table > tbody > tr:nth-child(2)'),page_check))
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
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)    
