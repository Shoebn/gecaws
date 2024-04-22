from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_comprarpub_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_comprarpub_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ar_comprarpub_spn'
    
    notice_data.main_language = 'ES'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'ARS'
        
    notice_data.notice_type = 4
    
    try: 
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try: 
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        document_opening_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:
        org_name =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if len(notice_data.local_title) < 5:
            return
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    try:
        detail_page = WebDriverWait(tender_html_element, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(1) > a")))
        page_main.execute_script("arguments[0].click();",detail_page)

        WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > section > div > div')))

        try:
            notice_url = page_main.current_url
            notice_data.notice_url =notice_url.split('|')[0].strip()
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
            pass 

        try:
            notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body > section > div > div').get_attribute("outerHTML")                     
        except:
            pass
        
        try:
            document_purchase_start_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Inicio de recepción de documentación:")]//following::div[1]').text
            document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
            notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass

        try:
            document_purchase_end_time = page_main.find_element(By.XPATH, '//*[contains(text(),"Fin de recepción de documentación:")]//following::div[1]').text
            document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
            pass
        
        try:
            notice_deadline = page_main.find_element(By.XPATH, '//*[contains(text(),"Fecha de apertura:")]//following::div[1]').text
            notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
    
        try:
            publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Fecha de publicación:")]//following::div[1]').text
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:  
            procurement_method1 = page_main.find_element(By.XPATH, '//*[contains(text(),"Alcance")]//parent::div[1]').text.split('Alcance:')[1].strip()
            procurement_method = GoogleTranslator(source='auto', target='en').translate(procurement_method1)
            if 'National' in procurement_method:
                 notice_data.procurement_method = 0
            elif 'International' in procurement_method:
                 notice_data.procurement_method = 1
            else:
                 notice_data.procurement_method = 2
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Monto estimado:")]//parent::div[1]').text.split('Monto estimado:')[1].strip()
            est_amount = re.sub("[^\d\.\,]", "",est_amount)
            notice_data.est_amount = float(est_amount.replace(',','.').strip())
            notice_data.grossbudgetlc = notice_data.est_amount
        except Exception as e: 
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass 

        try:
            notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Plazo de mantenimiento de la oferta:")]//parent::div[1]').text.split('Plazo de mantenimiento de la oferta:')[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__)) 
            pass 

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'AR'
            customer_details_data.org_language = 'ES'

            customer_details_data.org_name =  org_name

            try:
                org_address1 = page_main.find_element(By.XPATH, '//*[contains(text(),"Unidad Operativa de Contrataciones")]//following::div[1]').text
                org_address2 = page_main.find_element(By.XPATH, '//*[contains(text(),"Lugar de recepción de documentación física:")]//parent::div[1]').text.split('Lugar de recepción de documentación física:')[1].strip()
                customer_details_data.org_address = org_address1+','+org_address2
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__)) 
                pass 

            try:
                org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Contacto:")]//parent::div[1]').text.split('Contacto:')[1].strip()
                email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
                customer_details_data.org_email = email_regex.findall(org_email)[0]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__)) 
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass 

        try:
            lot_data = page_main.find_element(By.XPATH, '//*[contains(text(),"Renglones Convocatoria")]//following::div[1]')
            lot_number = 1
            for lots in lot_data.find_elements(By.CSS_SELECTOR, 'div.panel-body.bg-default > table > tbody > tr')[1:]:

                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                try:
                    lot_details_data.lot_actual_number =lots.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass     

                lot_details_data.lot_title = lots.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                try:
                    lot_details_data.lot_description = lots.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass     

                try:  
                    notice_data.category = page_main.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in category: {}".format(type(e).__name__))
                    pass
                try:
                    lot_quantity = lots.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                    lot_quantity = re.sub("[^\d\.\,]", "",lot_quantity)
                    lot_details_data.lot_quantity = float(lot_quantity.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass

        try:
            documents_data = page_main.find_element(By.XPATH, '//*[contains(text(),"Anexos")]//following::div[1]')
            for single_record in documents_data.find_elements(By.CSS_SELECTOR, 'div.panel-body.bg-default > div > table > tbody > tr')[1:]:
                attachments_data = attachments()

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")

                try:
                    attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except:
                    pass

                try:
                    attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                except:
                    pass

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
                
        detail_page_back = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"body > section > div > div > div.row > div > div > a")))
        page_main.execute_script("arguments[0].click();",detail_page_back)
        time.sleep(10)

        last_date = th.strftime('%d/%m/%Y')
        
        page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_devDteEdtFechaAperturaDesde_I"]').send_keys(last_date)
        time.sleep(3)
        
        two_months_date = th + timedelta(days=2*30)
        after_two_months_date = two_months_date.strftime('%d/%m/%Y')
        
        page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_devDteEdtFechaAperturaHasta_I"]').send_keys(after_two_months_date)
        time.sleep(3)

        Buscar_click = page_main.find_element(By.CSS_SELECTOR,'#ctl00_CPH1_btnListarPublicacionAvanzado').click()
        time.sleep(10)

    except Exception as e:
        logging.info("Exception in detail_page: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main =  fn.init_chrome_driver_head(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://comprar.gob.ar/BuscarAvanzadoPublicacion.aspx#"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)  
        
        select_Estado = Select(page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_ddlEstadoProceso"]'))
        select_Estado.select_by_index(1)
        time.sleep(5)
        
        last_date = th.strftime('%d/%m/%Y')
        
        page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_devDteEdtFechaAperturaDesde_I"]').send_keys(last_date)
        time.sleep(3)
        
        two_months_date = th + timedelta(days=2*30)
        after_two_months_date = two_months_date.strftime('%d/%m/%Y')
        
        page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_devDteEdtFechaAperturaHasta_I"]').send_keys(after_two_months_date)
        time.sleep(3)

        Buscar_click = page_main.find_element(By.CSS_SELECTOR,'#ctl00_CPH1_btnListarPublicacionAvanzado').click()
        time.sleep(7)
        
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#ctl00_CPH1_GridListaPliegos > tbody > tr:nth-child(3)'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos > tbody > tr')))
                length = len(rows)
                time.sleep(5)
                for records in range(1,length-1):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_CPH1_GridListaPliegos > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)

                    if notice_count >= MAX_NOTICES:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(10)     
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#ctl00_CPH1_GridListaPliegos > tbody > tr:nth-child(3)'),page_check))

                    try:
                        last_date = th.strftime('%d/%m/%Y')

                        page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_devDteEdtFechaAperturaDesde_I"]').send_keys(last_date)
                        time.sleep(3)

                        two_months_date = th + timedelta(days=2*30)
                        after_two_months_date = two_months_date.strftime('%d/%m/%Y')

                        page_main.find_element(By.XPATH,'//*[@id="ctl00_CPH1_devDteEdtFechaAperturaHasta_I"]').send_keys(after_two_months_date)
                        time.sleep(3)

                        Buscar_click = page_main.find_element(By.CSS_SELECTOR,'#ctl00_CPH1_btnListarPublicacionAvanzado').click()
                        time.sleep(7)
                    except:
                        pass
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
