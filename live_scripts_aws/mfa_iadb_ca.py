from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_iadb_ca"
log_config.log(SCRIPT_NAME)
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_iadb_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'mfa_iadb_ca'
    notice_data.main_language = 'ES'
    performance_country_data = performance_country()
    
    performance_country_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text.title()
    if 'Regional' in performance_country_1:
        performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)
    else:
        performance_country_data.performance_country = fn.procedure_mapping("assets/mfa_iadb_ca_all_countrycode.csv",performance_country_1)  
        notice_data.performance_country.append(performance_country_data)

    notice_data.notice_type = 7
    notice_data.procurement_method = 2

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.project_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').text
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = notice_no.split('-impact/')[1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass    

    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, '#block-outline-frontend-content > article').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    notice_data.currency = 'USD'
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'THE INTER-AMERICAN DEVELOPMENT BANK (IDB)'

        customer_details_data.org_country = fn.procedure_mapping("assets/mfa_iadb_ca_all_countrycode.csv",performance_country_1)  
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
    

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        
        try:
            award_details_data = award_details()
            award_details_data.bidder_name = 'N/A'

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        Cookies_close_click = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#onetrust-close-btn-container > button"))) 
        page_details.execute_script("arguments[0].click();",Cookies_close_click)
        time.sleep(5)
    except:
        pass

    try:
        Implementation_Phase_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div > idb-accordion > idb-accordion-panel:nth-child(1) > idb-heading")))  
        page_details.execute_script("arguments[0].click();",Implementation_Phase_click)
    except:
        pass
    try:
        Other_Documents_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div > idb-accordion > idb-accordion-panel:nth-child(2) > idb-heading")))  
        page_details.execute_script("arguments[0].click();",Other_Documents_click)
    except:
        pass
    try:
        Preparation_Phase_click = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div > idb-accordion > idb-accordion-panel:nth-child(3) > idb-heading")))  
        page_details.execute_script("arguments[0].click();",Preparation_Phase_click)
    except:
        pass
    
    try:
        Other_Documents_click = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div > idb-accordion > idb-accordion-panel:nth-child(4) > idb-heading")))  
        page_details.execute_script("arguments[0].click();",Preparation_Phase_click)
    except:
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > idb-accordion > idb-accordion-panel > idb-card-grid > idb-document-card'): 
            attachments_data = attachments()
        
            file_name = single_record.text
            if 'docx' in file_name:
                attachments_data.file_name = file_name.split('.docx')[0]
            elif 'doc' in file_name:
                attachments_data.file_name = file_name.split('.doc')[0]
            elif 'xlsx' in file_name:
                attachments_data.file_name = file_name.split('.xlsx')[0]
            elif 'pdf' in file_name:
                attachments_data.file_name = file_name.split('.pdf')[0]
            elif 'DOCX' in file_name:
                attachments_data.file_name = file_name.split('.DOCX')[0]
            elif 'DOC' in file_name:
                attachments_data.file_name = file_name.split('.DOC')[0]
            elif 'PDF' in file_name:
                attachments_data.file_name = file_name.split('.PDF')[0]
            elif 'XLSX' in file_name:
                attachments_data.file_name = file_name.split('.XLSX')[0]
            elif 'zip' in file_name:
                attachments_data.file_name = file_name.split('.zip')[0] 
            elif 'ZIP' in file_name:
                attachments_data.file_name = file_name.split('.ZIP')[0] 
            elif 'XLS' in file_name:
                attachments_data.file_name = file_name.split('.XLS')[0] 
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').get_attribute("innerHTML")
        
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
        
        Publication_date = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#collapsepublication-date > li:nth-child(2)')))
        page_main.execute_script("arguments[0].click();",Publication_date)
        time.sleep(5)
        
        Type = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(5) > div > i"))) 
        page_main.execute_script("arguments[0].click();",Type)
        time.sleep(5)

        Type_Award = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#collapsetype > li:nth-child(2)")))
        page_main.execute_script("arguments[0].click();",Type_Award)
        time.sleep(5)

        try:
            for page_no in range(2,9):
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
