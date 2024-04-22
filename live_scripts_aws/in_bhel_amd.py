from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_bhel_amd"
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
SCRIPT_NAME = "in_bhel_amd"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'in_bhel_amd'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 16

    try:
        notice_data.document_type_description = 'Corrigendum'
    except:
        pass

    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.split('Tender NIT Number :')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.related_tender_id = re.findall('GEM/\d+/\w/\d+',notice_data.related_tender_id)[0]
    except:
        pass
    

    try:
        document_opening_time1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        document_opening_time = re.findall(r'\d+-\d+-\d{4}',document_opening_time1)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%d-%m-%Y').strftime('%Y-%m-%d')
        deadline_date = re.findall(r'\d+-\d+-\d{4} \d+:\d+:\d+ [apAP][Mm]',document_opening_time1)[0]
        notice_data.notice_deadline = datetime.strptime(deadline_date, '%d-%m-%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass

    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2) a").get_attribute('href')
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        pass
    try:
        publish_date = page_details.find_elementfind_element(By.XPATH, '//*[contains(text(),"TENDER TITLE")]//following::td[1]').text
        publish_date = re.findall(r'\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"TENDER TITLE")]//following::td[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"TENDER DESCRIPTION")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"EMD VALUE")]//following::td[1]').text
    except:
        pass
    try:
        notice_data.document_cost = float(page_details.find_element(By.XPATH, '//*[contains(text(),"DOCUMENT VALUE")]//following::td[1]').text)
    except:
        pass

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_text = tender_html_element.get_attribute('outerHTML')
        notice_text1 = page_details.find_element(By.XPATH,'//*[@id="services"]/div').get_attribute('outerHTML')
        notice_data.notice_text = notice_text + notice_text1
    except:    
        notice_data.notice_text += page_details.find_element(By.XPATH,'//*[@id="services"]/div').get_attribute('outerHTML')
    
    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = 'Bharat Heavy Electricals Limited'
        customer_details_data.org_parent_id = '7235568'
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"CONTACT PERSON")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('_')[1]
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"ADDRESS")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"EMAIL")]//following::td[1]').text
            if '[dot]' in org_email:
                org_email=org_email.replace('[dot]','.')
            if '[at]' in org_email:
                 org_email=org_email.replace('[at]','@')
            customer_details_data.org_email = org_email
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"TELEPHONE NO.")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"FAX NO.")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Download Full Details of Tender")]//following::td[1]/div/a'):
            attachments_data = attachments()
        
            attachments_data.file_name = single_record.text 
            attachments_data.external_url = single_record.get_attribute('href') 
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bhel.com/index.php/corrigendum-"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#corrigendum-view-block > tbody tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#corrigendum-view-block > tbody tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#corrigendum-view-block > tbody tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#corrigendum-view-block > tbody tr'),page_check))
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
