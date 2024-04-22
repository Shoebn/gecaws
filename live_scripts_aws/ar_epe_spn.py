from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ar_epe_spn"
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ar_epe_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ar_epe_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ARS'
    notice_data.main_language = 'ES'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,' div.item-detalle span strong').text.split('Nº')[1]
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.item-detalle button').text
        notice_data.notice_title =  GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        document_type = tender_html_element.find_element(By.CSS_SELECTOR,' div.item-detalle span').text
        
        if 'Licitación Pública' in document_type:
            notice_data.document_type_description = 'Licitación Pública'
        if 'Concurso Privado' in document_type:
            notice_data.document_type_description = 'Concurso Privado'
        if 'Compra Menor' in document_type:
            notice_data.document_type_description = 'Compra Menor'
    except:
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,' div:nth-child(n) > span').text
        if 'Obras' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        if 'Servicios' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        if 'Materiales' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
    except:
        pass
    
    notice_text = tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'button.btn.enlace-apertura.btn-default')
        page_main.execute_script("arguments[0].click();",notice_url)
        notice_data.notice_url = page_main.current_url 
        time.sleep(5)


        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = "ENERGIA DE SANTA FE"
            customer_details_data.org_parent_id = "7570510"
            customer_details_data.org_email = "suppliers@epe.santafe.gov.ar"
            customer_details_data.org_phone = "(0342) 4505856"

            try:
                customer_details_data.org_address =  page_main.find_element(By.XPATH,' //*[contains(text(),"Dirección")]//following::li[1]').text
            except:
                pass
            try:
                customer_details_data.org_city =  page_main.find_element(By.XPATH,' //*[contains(text(),"Lugar")]//following::li[1]').text
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
            notice_deadline1 =  page_main.find_element(By.XPATH,' //*[contains(text(),"Fecha de Apertura")]//following::li[1]').text
            notice_deadline2 =  page_main.find_element(By.XPATH,' //*[contains(text(),"Hora Inicio")]//following::li[1]').text.split('hs')[0]
            notice_deadline =  notice_deadline1 + ' ' + notice_deadline2   
            notice_deadline = notice_deadline.strip()
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass
        if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
            return


        try:
            est_amount = page_main.find_element(By.CSS_SELECTOR,'span.etiqueta-presupuesto').text.split('$')[1]
            est_amount = est_amount.replace('.','').replace(',','.')
            notice_data.est_amount = float(est_amount)
            notice_data.grossbudgetlc = notice_data.est_amount
        except:
            pass

        try:              

            for single_record in page_main.find_elements(By.CSS_SELECTOR, '#__layout > div > div.container-fluid > div.app-apertura-ficha > div.container > div.row.detalle > div.col-md-12 div button'):
                attachments_data = attachments()
                attachments_data.file_name = single_record.text
                external_url = single_record
                page_main.execute_script("arguments[0].click();",external_url)
                time.sleep(5)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url= (str(file_dwn[0]))
                logging.info("external_url")
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.notice_text += notice_text
            notice_data.notice_text += page_main.find_element(By.XPATH,'//*[@id="__layout"]/div/div[1]/div[3]/div[3]/div[2]').get_attribute('innerHTML')
        except:
            pass
        try:
            clk=page_main.find_element(By.XPATH,'//*[@id="__layout"]/div/div[1]/div[3]/div[2]/div/button').click()
        except:
            pass
        time.sleep(5)

        try:
            clk=page_main.find_element(By.XPATH,'//button[@class="close"]').click()
        except:
            pass
        time.sleep(7)
    except:
        pass
    WebDriverWait(tender_html_element, 20).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#__layout > div > div.container-fluid > div.app-apertura > div.contenedor-aperturas.container > div > div.col-md-9 > div'),page_check))
        


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.epe.santafe.gov.ar/administracion/aperturas"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk=page_main.find_element(By.XPATH,"//button[@class='close']").click()
        except:
            pass
        try:
            clk=page_main.find_element(By.XPATH,'//*[@id="__layout"]/div/div[1]/div[3]/div[3]/div/div/div/ul/li[1]/a/font/font').click()
        except:
            pass

        try:
            for page_no in range(2,5): #5
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#__layout > div > div.container-fluid > div.app-apertura > div.contenedor-aperturas.container > div > div.col-md-9 > div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#__layout > div > div.container-fluid > div.app-apertura > div.contenedor-aperturas.container > div > div.col-md-9 > div')))
                length = len(rows)                                                                              
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#__layout > div > div.container-fluid > div.app-apertura > div.contenedor-aperturas.container > div > div.col-md-9 > div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 10).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#__layout > div > div.container-fluid > div.app-apertura > div.contenedor-aperturas.container > div > div.col-md-9 > div'),page_check))
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
