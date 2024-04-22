from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_merito"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_merito"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_merito'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    # Onsite Field -Tipo Atto
    # Onsite Comment -None
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Anno e Numero Registro
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Periodo Pubblicazioneda - a
    # Onsite Comment -take first date as publish_date from Periodo Pubblicazioneda - a

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.split('\n')[0].strip()
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Periodo Pubblicazioneda - a
    # Onsite Comment -take second date as notice_deadline from Periodo Pubblicazioneda - a

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.split('\n')[1].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.row-fluid').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Spesa prevista
    # Onsite Comment -None

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, "//*[contains(text(),'Spesa prevista')]//following::span[1]").text
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    
        customer_details_data.org_name = 'Province of Forlì-Cesena'
        customer_details_data.org_parent_id = '7798055'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.org_address = 'Piazza G. B. Morgagni, 9, 47121 Forlì (FC)'
        customer_details_data.org_phone = '+39 0543714111'
        customer_details_data.org_email = 'urp@provincia.fc.it'
    # Onsite Field -Dirigente
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Dirigente')]//following::span[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.dettaglio-pratica-rght > table > tbody > tr')[1:]:
            attachments_data = attachments()
        # Onsite Field -Titolo
        # Onsite Comment -split  file_type from Titolo

            try:                                                       
                file_type = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
                if 'pdf' in file_type or 'PDF' in file_type:
                    attachments_data.file_type = 'pdf'
                else:
                    attachments_data.file_type = 'none'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Titolo
        # Onsite Comment -split  file_name from Titolo

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        
        # Onsite Field -Descrizione
        # Onsite Comment -None
            attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
        # Onsite Field -Scarica
        # Onsite Comment -take only anchor tag data from this field
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
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
    urls = ['https://provincia-fc.trasparenza-valutazione-merito.it/web/trasparenza/dettaglio-trasparenza?p_p_id=jcitygovmenutrasversaleleftcolumn_WAR_jcitygovalbiportlet&p_p_lifecycle=0&p_p_state=Normal&p_p_mode=view&p_p_col_id=column-2&p_p_col_count=1&_jcitygovmenutrasversaleleftcolumn_WAR_jcitygovalbiportlet_current-page-parent=11745&_jcitygovmenutrasversaleleftcolumn_WAR_jcitygovalbiportlet_current-page=11778'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        iframe = page_main.find_element(By.XPATH,'//*[@id="corrente-iframe"]') 
        page_main.switch_to.frame(iframe) 

        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#selectPagination'))
        pp_btn.select_by_index(3)

        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="p_p_id_jcitygovalbopubblicazioni_WAR_jcitygovalbiportlet_"]/div/div[2]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="p_p_id_jcitygovalbopubblicazioni_WAR_jcitygovalbiportlet_"]/div/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="p_p_id_jcitygovalbopubblicazioni_WAR_jcitygovalbiportlet_"]/div/div[2]/table/tbody/tr')))[records]
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
