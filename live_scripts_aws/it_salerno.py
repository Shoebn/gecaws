from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_salerno"
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
SCRIPT_NAME = "it_salerno"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_salerno'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.document_type_description = 'Avvisi e Bandi'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if "AVVISO DI AGGIUDICAZIONE DI APPALTO" in notice_data.local_title:
            notice_data.notice_type = 7
        elif "MANIFESTAZIONE D'INTERESSE AZIONI " in notice_data.local_title:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        if 'PROCEDURA NEGOZIATA' in notice_data.local_title:
            notice_data.type_of_procedure_actual='PROCEDURA NEGOZIATA'
            notice_data.type_of_procedure = "Negotiated procedure"
        elif 'GARA A PROCEDURA' in notice_data.local_title:
            notice_data.type_of_procedure_actual='GARA A PROCEDURA'
            notice_data.type_of_procedure = "OPEN PROCEDURE" 
        else:
            notice_data.type_of_procedure_actual='Other'
            notice_data.type_of_procedure = "Other"
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d') 
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    logging.info(notice_data.publish_date)

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")  
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.review36').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div > div.campoOggetto').text.split('€')[1]
        notice_data.grossbudgetlc = re.sub("[^\d\.\,]","",notice_data.grossbudgetlc)
        notice_data.grossbudgetlc =float(notice_data.grossbudgetlc.replace(',','.').replace('.','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        detail1=tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > div a').get_attribute("href")                     
        fn.load_page(page_details1,detail1,80)
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Provincia di Salerno'
        customer_details_data.org_parent_id = '1340566'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'

        try:
            customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details1.find_element(By.XPATH, "//*[contains(text(),'Responsabile:')]//following::a[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, "//*[contains(text(),'Email:')]//following::a[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details1.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div > div.campoOggetto114').text.split('Telefono:')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > span').text.split('-')[-1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > a').text
        
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > span').text.split('- pdf')[0].split('-')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
            
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
page_details1 = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    
    for page_no in range(0,80,20):
        url='https://trasparenza.provincia.salerno.it/index.php?id_doc=0&id_cat=&id_oggetto=0&id_sezione=957&senso=cre&ordine=data_creazione&id_cat=&inizio='+str(page_no)+'&limite=20&esattamente=&gtp=1&id_cat=&id_criterio=&id_doc=&id_ente=41&id_oggetto=&id_sez_ori=&id_sezione=957&id_sond=&limite=20&ordina_oggetto=&ordine=data_creazione&purecontent=&senso=cre&template_ori=&gtp=1'
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details1.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
