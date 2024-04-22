from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_nsw_pp"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_nsw_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = "au_nsw_pp"
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'AUD'
    notice_data.procurement_method = 2
    notice_data.notice_type = 3
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, "div > dl > dd:nth-child(4)").text

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "li > p:nth-child(2)").text
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%B-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li > h3').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li').text.split('RFT ID: ')[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > dl > dd:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > div > a:nth-child(2)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section >div.nsw-wysiwyg-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > div > p.h2').text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        try:
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%B-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try: 
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Start date:")]//following::p[1]').text
        tender_contract_start_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMampm]+',tender_contract_start_date)[0]
        try:
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d-%B-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
        pass
    
    
    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"End date:")]//following::p[1]').text
        tender_contract_end_date = re.findall('\d+-\w+-\d{4} \d+:\d+ [PMAMampm]+',tender_contract_end_date)[0]
        try:
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d-%b-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d-%B-%Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.ID, 'main-content').text.split('Scope')[1].split('Instructions')[0]
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    customer_details_data = customer_details()
    customer_details_data.org_country = 'AU'
    customer_details_data.org_language = 'EN'
    customer_details_data.org_name = org_name
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'ul.margin-top--lg.nsw-link-list__list.padding-left--none a'):
            attachments_data = attachments()
            
            attachments_data.file_name = single_record.text
            if('.docx' in attachments_data.file_name):
                attachments_data.file_name = attachments_data.file_name.split('.docx')[0]
            elif('.pdf' in attachments_data.file_name):
                attachments_data.file_name = attachments_data.file_name.split('.pdf')[0]
            
            try:
                attachments_data.file_size = single_record.find_element(By.XPATH,'./following-sibling::div').find_element(By.CSS_SELECTOR,'span:nth-child(2)').text.split(', ')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            attachments_data.external_url = single_record.get_attribute('href')
            if('.pdf' in attachments_data.external_url):
                attachments_data.file_type = 'pdf'
            elif('.docx' in attachments_data.external_url):
                attachments_data.file_type = 'docx'
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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
    urls = ["https://suppliers.buy.nsw.gov.au/opportunity/search?query=&categories=&types=Schemes&page=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="search-results"]/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="search-results"]/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' li.nsw-pagination__item.nsw-pagination__item--next-page > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="search-results"]/ul/li'),page_check))
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
