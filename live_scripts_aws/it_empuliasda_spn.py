from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_empuliasda_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_empuliasda_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_empuliasda_spn'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.main_language = 'IT'
    
    notice_data.notice_type = 4
    
    # Onsite Field -Descrizione
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_m_g_08809ba0_add9_4194_92c5_cdebf3461d14_dgList  td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scadenza
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline1 = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_deadline2 = re.findall('\d+:\d+:\d+',notice_deadline)[0]
        notice_deadline = notice_deadline1+" "+notice_deadline2
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Scadenza
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')


    # Onsite Field - Data Pubblicazione	
    # Onsite Comment -click on "Tabella informativa di indicizzazione"

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Del:')]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, '#template_doc > thead > tr > th').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'EmPULIA - InnovaPuglia SpA'
        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(7) > td > table > tbody > tr'):
            attachments_data = attachments()
        # Onsite Field -ALLEGATO
        # Onsite Comment -None

            file_name = single_record.find_element(By.CSS_SELECTOR, 'td.linkAttachment').text
            if ".pdf" in file_name:
                attachments_data.file_name = file_name.replace(".pdf","").strip()
            elif ".zip" in file_name:
                attachments_data.file_name = file_name.replace(".zip","").strip()
            elif ".docx" in file_name:
                attachments_data.file_name = file_name.replace(".docx","").strip()
            else:
                attachments_data.file_name = file_name.replace(".pdf","").strip()

        # Onsite Field -ALLEGATO
        # Onsite Comment -None

            external_url = single_record.find_element(By.CSS_SELECTOR, 'td.linkAttachment label').get_attribute("onclick")
            attachments_data.external_url = external_url.split("window.open('")[1].split("') + '&FORMAT=I%2CN');")[0]

            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(1) > label').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

        # Onsite Field -ALLEGATO
        # Onsite Comment -split extension

            try:
                file_type = single_record.find_element(By.CSS_SELECTOR, 'td.linkAttachment').text
                if ".pdf" in file_type:
                    attachments_data.file_type = 'pdf'
                elif ".zip" in file_type:
                    attachments_data.file_type = 'zip'
                elif ".docx" in file_type:
                    attachments_data.file_type = 'docx'
                else:
                    attachments_data.file_type = 'pdf'
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.empulia.it/tno-a/empulia/Empulia/SitePages/Lista%20Bandi%20SDA.aspx"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_m_g_08809ba0_add9_4194_92c5_cdebf3461d14_dgList"]/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_m_g_08809ba0_add9_4194_92c5_cdebf3461d14_dgList"]/tbody/tr')))[records]
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
    
 
