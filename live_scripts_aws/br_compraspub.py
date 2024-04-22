from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "br_compraspub"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from selenium.webdriver.chrome.options import Options
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_compraspub"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    #after opening the url click on "Busca avançada" > then click on "Periodo" >  then select "Publicação"   > then select the date > then click on "BUSCAR" to take tender information.
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'br_compraspub'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'PT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BR'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BRL'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -take in text format

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.main-item > h2 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.main-item > div > span:nth-child(2) > span').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.main-item > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'section.container-fluid.sobre-processo').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nº do Processo:
    # Onsite Comment -notice_no split after "Nº do Processo:"

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Nº do Processo:")]').text.split(":")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data de Publicação:
    # Onsite Comment -take publication_date  “Data de Publicação: ” from this field .. split the date from same line.. take data  like “21/06/2023 às 01:30 " also remove the text like "às " between date and time.

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, 'div.content.main-left > div:nth-child(2) > div > p').text.split("Data de Publicação:")[1].split("\n")[0]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Limite p/ Recebimento das Propostas:
    # Onsite Comment -take notice_deadline  “Limite p/ Recebimento das Propostas: ” from this field .. split the date from same line.. take data  like “21/06/2023 às 01:30 " also remove the text like "às " between date and time.

    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, 'div.content.main-left > div:nth-child(2) > div > p').text.split('Limite p/ Recebimento das Propostas:')[1].split("\n")[0]
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -V. Referência
    # Onsite Comment -if value is not present in the field then take "none"

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'span.s12.half').text
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace('.','').replace(',','.').strip()
        notice_data.est_amount =float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
#         pass
    
    # Onsite Field -V. Referência
    # Onsite Comment -if value is not present in the field then take "none"

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None
    customer_details_data.org_country = 'BR'
    customer_details_data.org_language = 'PT'
    

    try:
        customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'span:nth-child(1) > s').text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass

    # Onsite Field -Autoridade Competente:
    # Onsite Comment -take contact_person  “Autoridade Competente: ” from this field .. split the contact_person name from same line and below the line also if available...

    try:
        customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.content.main-left > div:nth-child(1) > p').text.split("Autoridade Competente: ")[1].split("\n")[0]
    except Exception as e:
        logging.info("Exception in contact_person: {}".format(type(e).__name__))
        pass
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'section > div > div.lista-registros'):
            lot_details_data = lot_details()
        # Onsite Field -Descrição
        # Onsite Comment -None
            lot_details_data.lot_number = lot_number
            try:
                lot_title = single_record.find_element(By.CSS_SELECTOR, 'section > div.container > div.lista-registros > div.item > span:nth-child(2)').text
                lot_details_data.lot_title  = GoogleTranslator(source='auto', target='en').translate(lot_title)
            except:
                lot_details_data.lot_title = notice_data.notice_title
                notice_data.is_lot_default = True
        
        # Onsite Field -Descrição
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = lot_details_data.lot_title
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Unidade
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'section > div.container > div.lista-registros > div.item > span:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantidade
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'span.s11.half').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -V. Referência
        # Onsite Comment -if value is not present in the field then take "none"

            try:
                lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'span.s12.half').text
                lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                lot_details_data.lot_grossbudget_lc  =float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#detalhe-processo-page > div > main > section > section.container-fluid.sobre-processo > div > div.content.main-left > div.full-side > div:nth-child(4) > div')[1:]:
            attachments_data = attachments()
        # Onsite Field -Tipo
        # Onsite Comment -don't take "Tipo" in file_name.

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'span:nth-child(1)').text
        # Onsite Field -Documento
        # Onsite Comment -1.don't take "Documento" in file_description.    2.remove file extension from file_description.
            try:
                attachments_data.file_description = attachments_data.file_name
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

        # Onsite Field -Documento
        # Onsite Comment -1.don't take "Documento" in file_type.		2.take onle file extension in file_type.
            try:
                attachments_data.file_type = attachments_data.file_name.split(").")[1]
            except:
                attachments_data.file_type = attachments_data.file_name.split(".")[1]
        # Onsite Field -Download
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'span:nth-child(4) > div > a').get_attribute('href')        
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
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    
    today =date.today() 
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    url = "https://www.portaldecompraspublicas.com.br/processos?tipoData=2&dataInicial="+str(th)+"&dataFinal="+str(today)
    urls = [url] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'section.container-fluid > div > section > div > div > div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'section.container-fluid > div > section > div > div > div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'section.container-fluid > div > section > div > div > div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'section.container-fluid > div > section > div > div > div'),page_check))
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
    page_details.quit() 

    
    output_json_file.copyFinalJSONToServer(output_json_folder)
