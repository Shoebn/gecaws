from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "co_indumil_spn"
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
SCRIPT_NAME = "co_indumil_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'co_indumil_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CO'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'COP'
    
    notice_data.main_language = 'ES'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.notice_url = url 

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:
        grossbudgetlc  = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        grossbudgetlc = re.sub("[^\d\.\,]", "", grossbudgetlc)
        notice_data.grossbudgetlc =float(grossbudgetlc.replace('.','').replace(',','.').strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc : {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description : {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(7)').text
        if 'p. m.' in notice_deadline or 'a. m.' in notice_deadline:
            deadline = notice_deadline.replace('p. m.','pm').replace('a. m.','am').strip()
            notice_deadline1 = GoogleTranslator(source='es', target='en').translate(deadline)
            notice_deadline = re.findall('\w+ \d+, \d{4} \d+:\d+ [pmAMPMam]+',notice_deadline1)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if 'p. m.' in publish_date or 'a. m.' in publish_date:
            p_date = publish_date.replace('p. m.','pm').replace('a. m.','am').strip()
            publish_date1 = GoogleTranslator(source='es', target='en').translate(p_date)
            publish_date = re.findall('\w+ \d+, \d{4} \d+:\d+ [pmAMPMam]+',publish_date1)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%b %d, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return  

    try:
        notice_url = WebDriverWait(tender_html_element, 60).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(1) > input')))
        page_main.execute_script("arguments[0].click();",notice_url)
        time.sleep(7)
    except Exception as e:
        pass

    try:              
        customer_details_data = customer_details() 
        customer_details_data.org_name = "INDUMIL (Colombia)"
        customer_details_data.org_parent_id = 7612361
        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '(//*[contains(text(),"Ciudad")]//following::td[1])[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass  

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '(//*[contains(text(),"Dirección")]//following::td[1])[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass 
        customer_details_data.org_country = 'CO'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        start_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Fecha Inicial")]//following::td[2])[1]').text
        purchase_start_time = GoogleTranslator(source='es', target='en').translate(start_time)
        purchase_start_time1 = purchase_start_time.replace('-','').replace('.','') 
        document_purchase_start_time = re.findall('\w+ \d+, \d{4}',purchase_start_time1)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%b %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    try:
        end_time = page_main.find_element(By.XPATH, '(//*[contains(text(),"Fecha Final")]//following::td[3])[1]').text
        purchase_end_time = GoogleTranslator(source='es', target='en').translate(end_time)
        purchase_end_time1 = purchase_end_time.replace('-','').replace('.','')
        document_purchase_end_time = re.findall('\w+ \d+, \d{4}',purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%b %d, %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:  
        for single_record in page_main.find_elements(By.CSS_SELECTOR,'#MainContent_gvDocumentos > tbody > tr')[1:]:
            attachments_data = attachments()
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3) > a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += page_main.find_element(By.XPATH,'/html/body/form/div[3]').get_attribute('outerHTML')
    except:
        pass

    page_main.execute_script("window.history.go(-1)")
    time.sleep(2)
    WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#MainContent_gvProcesos > tbody > tr:nth-child(3)')))
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
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
    urls = ["https://www.indumil.gov.co/INDUMIL.Adquisiciones.Procesos/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#MainContent_gvProcesos > tbody > tr:nth-child(3)'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#MainContent_gvProcesos > tbody > tr')))
                length = len(rows)
                for records in range(2,length-1):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#MainContent_gvProcesos > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#MainContent_gvProcesos > tbody > tr:nth-child(3)'),page_check))
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