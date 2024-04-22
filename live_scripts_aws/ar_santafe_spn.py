from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_santafe_spn"
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
import re
#Note:First click "Para la Apertura" this and grab tha data. Than Second click "Más consultadas" this and grab the data.

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_santafe_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ar_santafe_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ARS'

    notice_data.main_language = 'ES'

    notice_data.notice_type = 4
    
    # Onsite Field -Gestión
    # Onsite Comment -Note:Take a number

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Gestión

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, ' //*[contains(text(),"Objeto de la gestión:")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.content-center > div.content-tramites-gray').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Fecha de Publicación:
#     # Onsite Comment -Note:Splite after "Fecha de Publicación:" this keyword

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha de Publicación:")]').text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Fecha y hora límite de presentación de ofertas:

    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Fecha y hora límite de presentación de ofertas:")]//following::div[1]').text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción:")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Alcance:
    # Onsite Comment -Note:If have this keywod start with "NACIONAL " than the  procurement_method will be "0" and start with "INTERNACIONAL" than the  procurement_method will be "1" other wise it will be "0"

    try:
        procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"Alcance:")]//following::div[1]').text
        if 'NACIONAL' in procurement_method:
            notice_data.procurement_method = 0
        elif 'INTERNACIONAL' in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 0
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Monto Original:
    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Monto Original:")]//following::div[1]').text
        est_amount = est_amount.replace('.','').replace(',','.').split('$ ')[1].strip()
        notice_data.est_amount = float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

#     # Onsite Field -Monto Original:
    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudget_lc: {}".format(type(e).__name__))
        pass    
    
#     # Onsite Field -Valor del pliego:
    try:
        document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Valor del pliego:")]//following::div[1]').text.split('$ ')[1].split('(')[0]
        try:
            notice_data.document_fee = document_fee.replace('.','').replace(',','.')
        except:
            notice_data.document_fee = document_fee
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Organismo Licitante
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text

    # Onsite Field -Lugar de presentación de ofertas:
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Lugar de presentación de ofertas:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Lugar de presentación de ofertas:
    # Onsite Comment -Note:Available than take

        try:
            org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Lugar de presentación de ofertas:")]//following::div[1]').text
            email_reg  =  r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            customer_details_data.org_email  = re.findall(email_reg , org_email )[0]
        except:
            pass

        customer_details_data.org_country = 'AR'
        customer_details_data.org_language = 'ES'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Documentos")]//following::a'):
            attachments_data = attachments()
        # Onsite Field -Documentos
        # Onsite Comment -Note:Take a both

            attachments_data.file_name = single_record.text
        # Onsite Field -Documentos

            attachments_data.external_url = single_record.get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        lot_details_data = lot_details()
    # Onsite Field -Rubros - Subrubros:
    # Onsite Comment -Note:Take only lots
        lot_details_data.lot_number=1
        lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Rubros - Subrubros:")]//following::div').text
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.santafe.gob.ar/index.php/web/guia/portal_compras?pagina=inicio&criterio=todas","https://www.santafe.gob.ar/index.php/web/guia/portal_compras?pagina=inicio&criterio=visitadas"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[4]/div[2]/div[1]/div/div[2]/div[2]/div/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[2]/div[1]/div/div[2]/div[2]/div/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div[2]/div[1]/div/div[2]/div[2]/div/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
