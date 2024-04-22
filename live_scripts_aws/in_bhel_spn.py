from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_bhel_spn"
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
SCRIPT_NAME = "in_bhel_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_bhel_spn'
    
    notice_data.main_language = 'EN'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'INR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = 'Tenders'
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-field-nit-no-').text
        if notice_data.notice_no == None:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' td.views-field.views-field-title > span:nth-child(2)').text.split('Tender Notification Number :')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -Publish Date 12-02-2024 03:47:31 PM
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td.views-field.views-field-title").text.split('Date of Notification :')[1].strip()
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+ [PMAMpmam]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        document_opening_time = re.findall('\d+-\d+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%m-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+ [PMAMpmam]+',notice_deadline)[0]
        notice_data.notice_deadline  = datetime.strptime(notice_deadline,'%d-%m-%Y %I:%M:%S %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title > span:nth-child(4) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,90)
        logging.info(notice_data.notice_url) 
        
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.bhel.mb-4.col-lg-12 > div > div:nth-child(2)').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            local_title = page_details.find_element(By.XPATH, "//*[contains(text(),'TENDER TITLE')]//following::td[1]").text
            if local_title != '-':
                notice_data.local_title = local_title
            notice_data.notice_title = notice_data.local_title
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        try:
            local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'TENDER DESCRIPTION')]//following::td[1]").text
            if local_description != '-':
                notice_data.local_description = local_description
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
        try:
            earnest_money_deposit = page_details.find_element(By.XPATH, "//*[contains(text(),'EMD VALUE')]//following::td[1]").text
            if earnest_money_deposit != '-':
                notice_data.earnest_money_deposit = earnest_money_deposit
        except Exception as e:
            logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
            pass
        
        try:
            document_cost = page_details.find_element(By.XPATH, "//*[contains(text(),'DOCUMENT VALUE')]//following::td[1]").text
            document_cost = re.sub("[^\d\.\,]","",document_cost)
            notice_data.document_cost =float(document_cost.replace('.','').replace(',','.').strip())
            notice_data.est_amount = notice_data.netbudgetlc
        except Exception as e:
            logging.info("Exception in document_cost: {}".format(type(e).__name__))
            pass
        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IN'
            customer_details_data.org_language = 'EN'
            customer_details_data.org_parent_id = 7235568
            customer_details_data.org_name = 'Bharat Heavy Electricals Limited'
            
            try:
                org_city1 = page_details.find_element(By.XPATH, "//*[contains(text(),'UNIT NAME')]//following::td[1]").text
                org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'UNIT NAME')]//following::td[1]").text.split(',')[-1].strip()
                if org_city != '-':
                    customer_details_data.org_city = org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
            
            try:
                org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'ADDRESS')]//following::td[1]").text
                if org_address != '-':
                    customer_details_data.org_address = org_address
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
            
            try:
                org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'EMAIL')]//following::td[1]").text.replace('[at]','@').replace('[dot]','.').strip()
                if org_email != '-':
                    customer_details_data.org_email = org_email
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
            
            try:
                org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'TELEPHONE NO.')]//following::td[1]").text
                if org_phone != '-':
                    customer_details_data.org_phone = org_phone
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            try:
                org_fax = page_details.find_element(By.XPATH, "//*[contains(text(),'FAX NO.')]//following::td[1]").text
                if org_fax != '--':
                    customer_details_data.org_fax = org_fax
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            try:
                contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'CONTACT PERSON')]//following::td[1]").text
                if contact_person != '--':
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try: 
            attach_data=page_details.find_element(By.XPATH, "//*[contains(text(),'Download Full Details of Tender')]//following::td[1]")
            for data in attach_data.find_elements(By.CSS_SELECTOR, "#adddownloadpdf > div > div"):
                attachments_data = attachments()
                attachments_data.file_name = data.find_element(By.CSS_SELECTOR, 'a').text
                
                try:
                    attachments_data.file_size = data.find_element(By.CSS_SELECTOR, 'span.file.file--mime-application-pdf.file--application-pdf').text
                except:
                    pass

                attachments_data.external_url = data.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                
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
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
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
    urls = ["https://www.bhel.com/index.php/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#block-friday-content > div > div > div > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#block-friday-content > div > div > div > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#block-friday-content > div > div > div > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#block-friday-content > div > div > div > nav > ul > li.pager__item.pager__item--next > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#block-friday-content > div > div > div > table > tbody > tr'),page_check))
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
