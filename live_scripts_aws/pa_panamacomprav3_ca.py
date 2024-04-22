#after opening the url click on "div.col-12.text-center.pt-3.pt-md-2 > button" button yo get data.
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pa_panamacomprav3_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pa_panamacomprav3_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'pa_panamacomprav3_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'ES'
  
    notice_data.currency = 'PAB'
    
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Modalidad de adjudicación
    # Onsite Comment -1.if "Global" is written then pass "1", otherwise pass "2".

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        if 'Global' in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Número
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descripción
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publicación
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Estado
    # Onsite Comment -if in document_type_description "Adjudicado=Awarded" is written then pass notice_type=7, and "Cancelado=Cancelled" is written then pass notice_type=16.

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        if 'Adjudicado' in notice_data.document_type_description:
            notice_data.notice_type = 7
        elif 'Cancelado' in notice_data.document_type_description:
            notice_data.notice_type = 16
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Número
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,90)
        logging.info(notice_data.notice_url)
        page_details.refresh()
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'ng-component > div > section').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Objeto de Contratación
    # Onsite Comment -1.repalce given keywords("Bien=Supply","Servicio=Service","Obra=Works")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Objeto de Contratación")]//following::td[1]').text
        if 'Bien' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Servicio' in  notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Obra' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Información General: >> Descripción
    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Descripción")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Aviso de convocatoria >> Monto de la contratación
    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Monto de la contratación")]//following::td[1]').text.split('B/.')[1].strip()
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(',','').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Condiciones de la solicitud : >> Días de entrega
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Días de entrega")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'PA'
        customer_details_data.org_language = 'ES'
        # Onsite Field -Entidad / Unidad de compra
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        
        # Onsite Field -Dependencia
        try:
            customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contacto de la unidad de compra: >> Nombre
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Nombre")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contacto de la unidad de compra: >> Teléfono
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Teléfono")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contacto de la unidad de compra: >> Correo electrónico
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Correo electrónico")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        # Onsite Field -Información de la entidad: >> Dirección de la unidad de compra
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Dirección de la unidad de compra")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -Documentos de la propuesta:
# Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/#/pliego-de-cargos/eyJwIjoicHJvY2Vzb1Zpc3RhUGxpZWdvIiwiaSI6NDQwNzIsInRwIjo0fQ"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#printProceso > div > field-archivos > div > table > tbody > tr'):
            attachments_data = attachments()

        # Onsite Field -Documentos de la propuesta: >> Tipo
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            
            try:
                attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass
        
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute('href')

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Razón Social")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in bidder_name: {}".format(type(e).__name__)) 
        pass
    
    try:
        address = page_details.find_element(By.XPATH, '//*[contains(text(),"Información del proponente:")]//following::td[4]').text
    except Exception as e:
        logging.info("Exception in award_adress: {}".format(type(e).__name__)) 
        pass
# Onsite Field -Ítems de la solicitud:
# Onsite Comment -ref_url:"https://www.panamacompra.gob.pa/Inicio/#/pliego-de-cargos/eyJwIjoicHJvY2Vzb1Zpc3RhUGxpZWdvIiwiaSI6NDQwNzIsInRwIjo0fQ"

    try:
        lot_number =1
        cpv_at_source = ''
        category = ''
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#printProceso > div > field-rubros > div > table > tbody > tr'):

             # Onsite Field -Ítems de la solicitud:	>> Código
            try:
                cpv_at_sources = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                cpv_at_source_regex = re.compile(r'\d{8}')
                cpv_list = cpv_at_source_regex.findall(cpv_at_sources)
                for code in cpv_list:
                    cpv_codes_list = fn.CPV_mapping("assets/pa_panamacomprav3_ca_cpv.csv",code)
                    for each_cpv in cpv_codes_list:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = each_cpv
                        cpv_at_source += each_cpv
                        cpv_at_source += ','
                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                pass

              # Onsite Field -Ítems de la solicitud: >> Clasificación
            try:
                category1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                category +=category1
                category +=','
            except Exception as e:
                logging.info("Exception in category: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            # Onsite Field -Ítems de la solicitud: >> Clasificación
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text

            # Onsite Field -Ítems de la solicitud: > Descripción
                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ítems de la solicitud: > Clasificación
                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ítems de la solicitud: > Unidad de Medida
                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ítems de la solicitud: > Precio Referencia
                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text.split('B/.')[1].strip()
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc.replace(',','').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ítems de la solicitud:	>> Código
                try:
                    lot_cpv_at_source1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_cpv_code_re= re.compile(r'\d{8}')
                    cpv_list = lot_cpv_code_re.findall(lot_cpv_at_source1)
                    lot_cpv_at_source = ''
                    for code in cpv_list:
                        cpv_codes_list = fn.CPV_mapping("assets/pa_panamacomprav3_ca_cpv.csv",code)
                        for each_cpv1 in cpv_codes_list:
                            lot_cpv_at_source += each_cpv1
                            lot_cpv_at_source += ','
                    lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
                except Exception as e:
                    logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_cpv_code_re= re.compile(r'\d{8}')
                    cpv_list = lot_cpv_code_re.findall(lot_cpv_code)
                    for code in cpv_list:
                        cpv_codes_list = fn.CPV_mapping("assets/pa_panamacomprav3_ca_cpv.csv",code)
                        for each_cpv in cpv_codes_list:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = each_cpv
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Información del proponente:
                try:
                    award_details_data = award_details()

                    # Onsite Field -Información del proponente: >> Razón Social

                    award_details_data.bidder_name = bidder_name

                    # Onsite Field -Información del proponente: >> Dirección
                    try:
                        award_details_data.address = address
                    except:
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
            except Exception as e:
                logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                pass
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.category = category.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpv_data: {}".format(type(e).__name__)) 
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
    urls = ["https://www.panamacompra.gob.pa/Inicio/#/busqueda-avanzada?q=eyJudW1MYyI6IjIwMjMtMC0wNy0xMi0wOC1DTS0wMzc3NTkifQ"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            close_popup = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/ngb-modal-window/div/div/ng-component/button')))
            page_main.execute_script("arguments[0].click();",close_popup)
            time.sleep(5)
        except:
            pass
        
        buscar = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.col-12.text-center.pt-3.pt-md-2 > button')))
        page_main.execute_script("arguments[0].click();",buscar)
        time.sleep(10)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.table-responsive > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.table-responsive > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.table-responsive > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.table-responsive > table > tbody > tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
