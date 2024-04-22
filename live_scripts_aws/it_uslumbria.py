from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_uslumbria"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import dateparser
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_uslumbria"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_uslumbria'
    
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if 'Manifestazione di Interesse' in notice_type:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text      
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline = dateparser.parse(notice_deadline)
        notice_data.notice_deadline = notice_deadline.strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = notice_type
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass



    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        est_amount = re.findall('\d+\D',est_amount)
        est_amount = ",".join(est_amount)
        notice_data.est_amount =float(est_amount.replace('.,','').replace(',,','.').replace(',','').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        vat = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if '22%' in vat:
            notice_data.vat = float(22)
        else:
            notice_data.vat = float(0)
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
        
    try:
        clk=WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="iubenda-cs-banner"]/div/div/div/div[3]/div[2]/button[2]'))).click()
    except:
        pass
    
    try:
        notice_data.notice_text += WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.span-18'))).get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "#ctl00_cphBody_divPubblicazioneBottom").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'AZIENDA UNITÀ SANITARIA LOCALE UMBRIA N. 2'
        customer_details_data.org_parent_id = '6803068'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
        
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.atto div a'):
            
            name = single_record.text
            if name =='':
                pass 
            else:
                attachments_data = attachments()
                attachments_data.file_name = name
      
                try:
                    attachments_data.file_type = single_record.text.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass
    
                attachments_data.external_url = single_record.get_attribute('href')
    
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
    urls = ["https://www.uslumbria2.it/amministrazione-trasparente/bandi-di-gara-e-contratti"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
    
        try:
            clk=WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' button.iubenda-cs-accept-btn.iubenda-cs-btn-primary'))).click()
            time.sleep(10)
        except:
            pass
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table.table-atti > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table-atti > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table.table-atti > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl00_cphBody_mcsElencoBandiGara_btnNextPage"]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table.table-atti > tbody > tr:nth-child(2)'),page_check))
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
