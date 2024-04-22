from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_cittametro"
log_config.log(SCRIPT_NAME)
import re
import jsons
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
SCRIPT_NAME = "it_cittametro"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.script_name ='it_cittametro'
    notice_data.notice_type = 4
    notice_data.procurement_method = 2
    notice_data.document_type_description='Announcement'
    notice_data.additional_source_name = 'serviziocontrattipubblici'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title : {}".format(type(e).__name__))
        pass        

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline_date= re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_deadline_time= re.findall('\d+:\d+',notice_deadline)[0]
        notice_deadline_concat=notice_deadline_date+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline_concat,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline : {}".format(type(e).__name__))
        pass
    logging.info(notice_data.notice_deadline)
    
    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(5)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount) 
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount : {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.GR0_GridCol_Link > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text = page_details.find_element(By.CSS_SELECTOR, '#accordion').get_attribute("outerHTML")
    except:
        logging.info("Exception in notice_text : {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'thead > tr > th > h1').text.split('(')[1].split(')')[0]
    except Exception as e:
        logging.info("Exception in notice_no : {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Altro indirizzo web')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in additional_tender_url : {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Città Metropolitana di Reggio Calabria'
        customer_details_data.org_parent_id = 7797534
        customer_details_data.org_country = 'IT'

        try:
            customer_details_data.org_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Ente Proponente')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_description : {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Incaricato:')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in contact_person : {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, "//*[contains(text(),'Indirizzo Web')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_website : {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, "//*[contains(text(),'Tipo di Amministrazione')]//following::td[4]").text
        except Exception as e:
            logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details : {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Scarica Allegati'
        attachments_data.file_description = "Scarica Allegati"
        attachments_data.file_type = "zip"
        number = notice_data.notice_url.split('&bando=')[1].split('&')[0]
        external_url = page_details.find_element(By.CSS_SELECTOR, 'input#DownloadAllegati').get_attribute('onclick').split("'")[1].split("'")[0]
        attachments_data.external_url = external_url+number
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments : {}".format(type(e).__name__)) 
        pass

    try:              
        tender_criteria_data = tender_criteria()
        tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, "//*[contains(text(),'Criterio Aggiudicazione:')]//following::td[1]").text
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria : {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Tipo Appalto:')]//following::td[1]").text
        if "Lavori pubblici" in notice_contract_type:
            notice_data.notice_contract_type="Works"
        elif "Servizi" in notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif "fornitura" in notice_contract_type:
            notice_data.notice_contract_type="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type : {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Data Pubblicazione')]//following::td[11]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://garetelematiche.cittametropolitana.rc.it/portale/index.php/bandi"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table-lista-bandi"]/tbody/tr')))
            length =len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table-lista-bandi"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
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
