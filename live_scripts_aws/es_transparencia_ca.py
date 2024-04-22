from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_transparencia_ca"
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
SCRIPT_NAME = "es_transparencia_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'es_transparencia_ca'
    notice_data.main_language = 'ES'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.notice_url = url
    
    # Onsite Field -Título
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td#tituloColumna').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Fecha de adjudicación
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR,"td#fechaAdjudicacionColumna").text
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
        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'
        
    # Onsite Field -Ministerio
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td#ministerioColumna').text       

    # Onsite Field -Órgano de contratación
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.CSS_SELECTOR,'td#organoContratacionColumna').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try: 
        notice_url = WebDriverWait(tender_html_element, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#tituloColumna > a'))).click()
        time.sleep(3)
        
        wait = WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Número de expediente')]//following::p"))).text
        
        try:
            notice_data.netbudgeteuro=page_main.find_element(By.XPATH,"//*[contains(text(),'Importe de licitación (sin impuestos)')]//following::p[1]").text.split('€')[0]
            notice_data.netbudgeteuro=notice_data.netbudgeteuro.replace('.','').replace(',','.')
            notice_data.netbudgeteuro = float(notice_data.netbudgeteuro)
            notice_data.est_amount = notice_data.netbudgeteuro
            notice_data.netbudgetlc = notice_data.netbudgeteuro
        except:
            pass
        
        try:
            notice_contract_type = page_main.find_element(By.XPATH,"//*[contains(text(),'Tipo de contrato')]//following::p[1]").text
            if 'Suministros' in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            elif 'Obras' in notice_contract_type or 'Concesión de Obras Públicas' in notice_contract_type or 'Concesión de Obras' in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            elif 'Servicios' in notice_contract_type or 'Concesión de Servicios' in notice_contract_type or 'Colaboración entre el sector público y sector privado' in notice_contract_type or 'Administrativo especial' in notice_contract_type :
                notice_data.notice_contract_type = 'Service'
            else:
                pass
        except:
            pass

        
        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#content_main > section').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.document_type_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Instrumentos de publicación')]//following::p").text.split('-')[1]
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Número de expediente
        # Onsite Comment -None
        
        try:
            notice_data.notice_no = page_main.find_element(By.XPATH, "//*[contains(text(),'Número de expediente')]//following::p").text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        
        lot1=page_main.find_element(By.XPATH, '//*[@id="content_main"]/section/article').text
        if 'Adjudicatario:' in lot1:
            try:
                lot_details_data = lot_details()
                lot_details_data.lot_number= 1
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True

                lot_details_data.contract_type = notice_data.notice_contract_type

                award_details_data = award_details()

                # Onsite Field -Adjudicatario:
                # Onsite Comment -None

                award_details_data.bidder_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Adjudicatario:')]//following::p[1]").text

                # Onsite Field -Duración del contrato
                # Onsite Comment -None
                award_details_data.contract_duration = page_main.find_element(By.XPATH, "//*[contains(text(),'Duración del contrato')]//following::p[1]").text.strip()
                notice_data.contract_duration=award_details_data.contract_duration

                # Onsite Field -Importe de adjudicación
                # Onsite Comment -None
                try:
                    netawardvalueeuro = page_main.find_element(By.XPATH, "//*[contains(text(),'Importe de adjudicación')]//following::p[1]").text.split('€')[0]
                    netawardvalueeuro = re.sub("[^\d\.\,]","",netawardvalueeuro)
                    award_details_data.netawardvalueeuro =float(netawardvalueeuro.replace('.','').replace(',','.').strip())
                    award_details_data.netawardvaluelc = award_details_data.netawardvalueeuro
                except:
                    pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)


                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
            
        WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="side_right"]/div/ul/li/p[2]/a'))).click()
        
        WebDriverWait(page_main, 60).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/section/article/div[6]/div/table/tbody/tr"))).text    
        
    except:
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://transparencia.gob.es/servicios-buscador/buscar.htm?categoria=licitaciones&lang=es"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,50):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/div/section/article/div[6]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div/section/article/div[6]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div/div/section/article/div[6]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div/div/section/article/div[6]/div/table/tbody/tr'),page_check))
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
