from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_juntadecia"
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
SCRIPT_NAME = "es_juntadecia"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'es_juntadecia'
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text
        notice_contract_type = GoogleTranslator(source='es', target='en').translate(notice_contract_type)
        if('service' in notice_contract_type or 'Plays' in notice_contract_type or 'Services' in notice_contract_type):
            notice_data.notice_contract_type = 'Service'
        if('supplies' in notice_contract_type):
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
     
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#j_idt21 > fieldset').get_attribute("outerHTML")                     
    except:
        pass
    
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Número de expediente")]//following::div[1]').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('-')[1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Título de expediente")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Últimas modificaciones")]//following::p[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe de licitación (CON IVA")]//following::span').text
        grossbudgetlc = GoogleTranslator(source='es', target='en').translate(grossbudgetlc)
        notice_data.grossbudgetlc = grossbudgetlc.split('.')[0].replace(',','').replace('€','')
        notice_data.grossbudgetlc = float(notice_data.grossbudgetlc)
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
 
    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importe de licitación (SIN IVA")]//following::span').text
        netbudgetlc = GoogleTranslator(source='es', target='en').translate(netbudgetlc)
        notice_data.netbudgetlc = netbudgetlc.split('.')[0].replace(',','').replace('€','')
        notice_data.netbudgetlc = float(notice_data.netbudgetlc)
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
     
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procedimiento")]//following::div[1]').text
        type_of_procedure_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/es_juntadecia_procedure.csv",type_of_procedure_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        document_type_description = page_details.find_element(By.CSS_SELECTOR, '#miga > div > div > a:nth-child(2)').text
        notice_data.document_type_description = GoogleTranslator(source='es', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción :")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duración del contrato")]//following::div[1]').text
        if contract_duration != 'Ver lotes':
            notice_data.contract_duration = GoogleTranslator(source='es', target='en').translate(contract_duration)
        else:
            pass     
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Clasificación CPV")]//following::ul[1]/li'):
            cpvs_data = cpvs()
            cpvs_data.cpv_code = single_record.text.split('-')[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
  
    try:              
        tender_criteria_data = tender_criteria()
        tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Criterios de adjudicación")]//following::p[1]').text
        tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        click=page_details.find_element(By.XPATH, '//*[contains(text(),"Información de lotes licitados")]//following::a[1]')
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(2)
        lots_path = page_details.find_element(By.XPATH, '//*[contains(text(),"Información de lotes licitados")]//following::div[1]').text
        lots =lots_path.split("Lote")
        lot_number=1
        for lot in lots[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number =  lot_number
            
            try:
                lot_details_data.lot_title = lot.split("Título :")[1].split("\n")[1].split("\n")[0]
                lot_details_data.lot_title_english = GoogleTranslator(source='es', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                lot_details_data.lot_title=notice_data.notice_title
                notice_data.is_lot_default = True
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_actual_number = lot.split("Nº de lote :")[1].split("\n")[1].split("\n")[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            
            try:
                contract_duration = lot.split("Duracion :")[1].split("\n")[1].split("\n")[0]
                lot_details_data.contract_duration = GoogleTranslator(source='es', target='en').translate(contract_duration)
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
            try:
                lot_no= lot.split("CPV :")[1].split("\n")[1].split("Lugar de ejecución :")[-1].strip()
                cpv_regex = re.compile(r'\d{8}')
                cpvs_data = cpv_regex.findall(lot_no)
                for cpv in cpvs_data:
                    if cpv == "":
                        return
                    elif cpv!= "":
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = cpv
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    else:
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                        
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
            
            try:
                lot_netbudget_lc= lot.split("Importe lote (sin IVA)")[1].split("\n")[1].split("\n")[0]
                lot_netbudget_lc = lot_netbudget_lc.replace('.','').replace(',','.').replace('€','')
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc)
                logging.info('lot netbudget: ' +str(lot_details_data.lot_netbudget_lc))
            except Exception as e:
                lot_details_data.lot_netbudget_lc = notice_data.netbudgetlc
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass

            try:
                lot_grossbudget_lc = lot.split("Importe lote (con IVA)")[1].split("\n")[1].split("\n")[0]
                lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').replace('€','')
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                logging.info('lot grossbudget: ' +str(lot_details_data.lot_grossbudget_lc))
            except Exception as e:
                lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.XPATH, '//*[contains(text(),"Número de lotes :")]//following::div[1]').text
                logging.info('lot quantity: '  +lot_details_data.lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        docs_btn = page_details.find_element(By.XPATH, '//*[contains(text(),"Anuncios publicados")]//following::a[1]')
        page_details.execute_script("arguments[0].click();",docs_btn)
        time.sleep(5)

        docs_path = page_details.find_element(By.XPATH, '//*[contains(text(),"Anuncios publicados")]//following::div[1]')
        for doc in docs_path.find_elements(By.CSS_SELECTOR, '#cuerpo ul > li')[1:-1]:
            attachments_data = attachments()
            
            attachments_data.file_type = 'pdf'
            attachments_data.file_name = doc.find_element(By.CSS_SELECTOR, 'p').text
            attachments_data.external_url = doc.find_element(By.CSS_SELECTOR,'#cuerpo  li > p > a:nth-child(1)').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        Importes = page_details.find_element(By.XPATH, '//*[contains(text(),"Importes")]')
        page_details.execute_script("arguments[0].click();",Importes)
        time.sleep(2)
        notice_data.notice_text = page_details.find_element(By.XPATH, '//*[@id="cuerpo"]/div[5]').get_attribute('outerHTML')
    except:
        pass
    
    
    try:
        Estado_del_expediente = page_details.find_element(By.XPATH, '//*[contains(text(),"Estado del expediente")]')
        page_details.execute_script("arguments[0].click();",Estado_del_expediente)
        time.sleep(2)
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="cuerpo"]/div[7]').get_attribute('outerHTML')
    except:
        pass
    
    try:
        Requisitos = page_details.find_element(By.XPATH, '//*[contains(text(),"Requisitos, criterios y condiciones")] ')
        page_details.execute_script("arguments[0].click();",Requisitos)
        time.sleep(2)
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="cuerpo"]/div[21]').get_attribute('outerHTML')
    except:
        pass

    try:
        details_1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Órgano de contratación :")]//following::div//a').get_attribute('href')
        fn.load_page(page_details1,details_1,80)
        WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.ID, 'cuerpo')))
    except Exception as e:
        logging.info("Exception in details_1: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'

        try:
            customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Denominación:")]//following::div[1]').text
        except:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
            
        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Dirección:")]//following::div[1]').text.strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Datos de contacto:")]//following::p[2]').text.split('Fax:')[0].split(':')[1].replace('|','').strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Datos de contacto:")]//following::p[2]').text.split('Fax:')[1].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::a[1]').text.strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details1.find_element(By.XPATH, '//*[contains(text(),"Datos de contacto:")]//following::p').text.strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.juntadeandalucia.es/haciendayadministracionpublica/apl/pdc_sirec/perfiles-licitaciones/licitaciones-publicadas.jsf"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tablaLicitacionesPublicadas"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tablaLicitacionesPublicadas"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tablaLicitacionesPublicadas"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tablaLicitacionesPublicadas"]/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info('No new record')
            break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    logging.info("Exception:"+str(e))
    raise e
    
finally:
    page_main.quit()
    page_details.quit() 
    page_details1.quit()   
    output_json_file.copyFinalJSONToServer(output_json_folder)
