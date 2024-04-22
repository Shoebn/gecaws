from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_iadb_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_iadb_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

# ----------------------------------------------------------------------------------------------------------------------------------------------------------

#      Go to URL : "https://projectprocurement.iadb.org/en/procurement-notices"
        
#      click on "Notices" Drop down and select "Current" for current details
# ----------------------------------------------------------------------------------------------------------------------------------------------------------

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
  
    notice_data.script_name = 'mfa_iadb_spn'
    
    notice_data.main_language = 'ES'
    
    notice_data.currency = 'USD'
   
    notice_data.procurement_method = 2
    
    notice_data.document_type_description = 'Procurement Notices'
    
    # Onsite Field -None
    # Onsite Comment -if "Notice Title" ( selector :  tr > th:nth-child(3) ) field has "UPDATE" Keyword then take notice_type = 16
    
    # Onsite Field -Notice Title
    # Onsite Comment -take "local_title" in a text format

    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(3)').text
        notice_data.local_title = local_title
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if 'UPDATE' in local_title.upper():
            notice_data.notice_type = 16
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Number
    # Onsite Comment -take notice_no in text_format

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(5)').text
    except:
        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(5) > a').get_attribute("href").split('/')[-1].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    try:
        performance_country_data = performance_country()
        performance_country_data.performance_country = notice_data.notice_no.split('-')[0].strip()
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        logging.info("Exception in performance_country_data: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.project_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publication Date
    # Onsite Comment -None November 15, 2023

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td:nth-child(6)").text
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Due Date
    # Onsite Comment -if notice_deadline is not available then take notice_deadline as a threshold date

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr> td:nth-child(7)").text
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Number
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr> td:nth-child(5) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="onetrust-accept-btn-handler"]'))).click()
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'article > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'THE INTER-AMERICAN DEVELOPMENT BANK (IDB)'
        customer_details_data.org_country =notice_data.notice_no.split('-')[0].strip()
        customer_details_data.org_language = 'ES'
        customer_details_data.org_parent_id = '7466022'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = 7466022
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    for CLICK in page_details.find_elements(By.XPATH, '//idb-accordion-panel[@variant="cards"]'):
        CLICK.click()
        time.sleep(2)
        
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'idb-card-grid > idb-document-card'):
            attachments_data = attachments()

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').get_attribute("innerHTML")

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3)').text

            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
            except:
                pass
            # Onsite Field -Project Documentation >> "Implementation Phase" ,  "Preparation Phase" , "Other Documents"
            # Onsite Comment -None

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://projectprocurement.iadb.org/en/procurement-notices"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            notice = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#cookiesjsr > div > div > div.cookiesjsr-banner--action > button.cookiesjsr-btn.important.allowAll'))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            YEAR = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="collapsepublication-date"]/li[2]'))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            notice = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#procurement-notices-body > div > div > div > div.col-xs-12.col-lg-3.col-sm-12.px-5 > div.container > div:nth-child(4) > div'))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        
        try:
            current = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="collapsenotices"]/li[2]'))).click()
            time.sleep(5)
        except:
            pass
        
        try:
            notice = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#procurement-notices-body > div > div > div > div.col-xs-12.col-lg-3.col-sm-12.px-5 > div.container > div:nth-child(5) > div'))).click()
            time.sleep(5)
        except Exception as e:
            logging.info("Exception in click: {}".format(type(e).__name__))
            pass
        try:
            GENRAL = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="collapsetype"]/li[3]'))).click()
            time.sleep(5)
        except:
            pass
        
        try:
            SPECIFIC = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="collapsetype"]/li[4]'))).click()
            time.sleep(5)
        except:
            pass

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tabledatanotices"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabledatanotices"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tabledatanotices"]/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tabledatanotices"]/tbody/tr'),page_check))
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
