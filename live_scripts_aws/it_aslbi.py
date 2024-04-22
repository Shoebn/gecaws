from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_aslbi"
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
SCRIPT_NAME = "it_aslbi"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
  
    notice_data.main_language = 'IT'
    
    notice_data.script_name = 'it_aslbi'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if publish_date "Da (Data inizio):" and  notice_deadline "A (Data fine):" both are not present in the field then take notice_type=2.otherwise notice_type=4.
    
    # Onsite Field -None
    # Onsite Comment -take only text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.wpb_wrapper > div > a').text
        if notice_data.local_title == "" or notice_data.local_title == None:
            return
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass    
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(4) > div:nth-child(1) > p").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    logging.info(notice_data.publish_date)
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Modalità di affidamento:
    # Onsite Comment -type_of_procedure_actual split after "Modalità di affidamento:"
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(5) > div > p").text.split("Modalità di affidamento:")[1]
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_aslbi_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -A (Data fine):
    # Onsite Comment -1.notice_deadline split after "A (Data fine):" 		2.if the "A (Data fine):" {notice_deadline} filed is blank. then take notice_deadline as a threshold date (10 days) from the current date.if notice_type=4. 		3.if notice_type=2 then take notice_deadline as threshold date 1 year after the publish_date.

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(4) > div:nth-child(2) > p").text
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if (notice_data.publish_date == "" or notice_data.publish_date == None)  and (notice_data.notice_deadline == "" or notice_data.notice_deadline == None):
        notice_data.notice_type = 2
    else:
        notice_data.notice_type = 4
        
    # Onsite Field -CIG
    # Onsite Comment -None
    
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' section > div > div > div > div > div:nth-child(n) > div:nth-child(2)  > div').text.split("CIG: ")[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.wpb_wrapper > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
        
    try:  
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#wt-cli-accept-btn")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(2)
    except:
        pass
    
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.entry-content')))
    except:
        pass

  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.entry-content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

        # Onsite Field -Importo di aggiudicazione:
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, '  div > section > table:nth-child(2) > tbody > tr:nth-child(5) > td:nth-child(2)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','.').replace('.','').strip()) 
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo di aggiudicazione:
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        # Onsite Field -None
        # Onsite Comment -don't take number in org_name
        customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, ' div > section > table:nth-child(2) > tbody > tr:nth-child(2)').text.split("Struttura proponente:")[1].split("\n")[0]
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div > div > ul > li'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.take only text   2.grab only possible
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, ' a').text
        # Onsite Field -None
        # Onsite Comment -1.grab only possible
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a').get_attribute('href')
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    for page_no in range(1,5):
        url = 'https://aslbi.piemonte.it/utilita/bandi-di-gara/page/'+str(page_no)+'/'
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#wt-cli-accept-btn")))
            page_main.execute_script("arguments[0].click();",click)
            time.sleep(2)
        except:
            pass
        
        try:
            WebDriverWait(page_details, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.wpb_wrapper > div > a')))
        except:
            pass

        try:
            rows = WebDriverWait(page_main, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.br-10.p-3.b-sh.mb-3')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.br-10.p-3.b-sh.mb-3')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
