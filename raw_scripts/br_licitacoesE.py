from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "br_licitacoesE"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()



# 1.after opening the url click on "Pesquisa avançada = li.menu_separador > a ". 
# 2.Then in "Comprador" select "Todos os compradores" and in "Situação da licitação" select "Publicada". 
# 3.After that fill the captch in given field "#pQuestionAvancada".
# 4.After selecting all the field and filling the captch click on "pesquisar = div:nth-child(16) > input".
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'br_licitacoesE'
    
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
    notice_data.notice_type = 4
    
    # Onsite Field -Descrição
    # Onsite Comment -1.take in text format.

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrição
    # Onsite Comment -1.take in text format.

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nº Edital :
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > b:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.to go on page_details click on notice_url check mark the "I'm not a robot = div.recaptcha-checkbox-border". Then solve the captcha. After that click on "Continuar" button.

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#total > div.geral').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Idioma da licitação
    # Onsite Comment -1.Replace main_language with given keyword("Português=PT").

    try:
        notice_data.main_language = page_main.find_element(By.XPATH, '//*[contains(text(),"Idioma da licitação")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in main_language: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Abrangência da disputa
    # Onsite Comment -1.Replace procurement_method with given number("Nacional=0").

    try:
        notice_data.procurement_method = page_main.find_element(By.XPATH, '//*[contains(text(),"Abrangência da disputa")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Tipo")]//following::div[12]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data de publicação
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),"Data de publicação")]//following::div[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Limite acolhimento de propostas
    # Onsite Comment -None

    try:
        notice_deadline = page_main.find_element(By.XPATH, "//*[contains(text(),"Limite acolhimento de propostas")]//following::div[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#divConsultarDetalhesLicitacao > fieldset'):
            customer_details_data = customer_details()
        # Onsite Field -Comprador
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Idioma da licitação
        # Onsite Comment -None

            try:
                customer_details_data.org_language = page_main.find_element(By.XPATH, '//*[contains(text(),"Idioma da licitação")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_language: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Pregoeiro
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Pregoeiro")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'BR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -1.to get lot_details click on "Opções >> Consultar lotes" in page main. 	2.Then fill the captch "//*[@id="inputCaptchaConsultarLotes"]".	and click on "continuar".

    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[@id="id_listagem"]'):
            lot_details_data = lot_details()
        # Onsite Field -Resumo do lote
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Resumo do lote")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Resumo do lote
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Resumo do lote")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.CSS_SELECTOR, '#id_listagem > div > div > fieldset > legend').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -Valor estimado do lote
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_main.find_element(By.XPATH, '//*[contains(text(),"Valor estimado do lote")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_main.find_elements(By.CSS_SELECTOR, '//*[@id="id_listagem"]'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Critério de seleção
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = page_main.find_element(By.CSS_SELECTOR, '//*[contains(text(),"Critério de seleção")]//following::div[1]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -1.to get lot_details click on "Opções >> Listar documentos" in page main.	//*[@id="inputCaptchaAnexosLicitacao"].	 2.Then fill the captch "//*[@id="inputCaptchaAnexosLicitacao"]".and click on "continuar".

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#local > div > fieldset'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.split file_name. eg.,here "EDITAL_PESRP_015_2023.PDF" take only "EDITAL_PESRP_015_2023" in file_name.

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, '#tDocumento > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split file_type. eg.,here "EDITAL_PESRP_015_2023.PDF" take only ".PDF" in file_type.

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, '#tDocumento > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.to download document check "#numeroAnexoLicitacao" this radio buutton. 		2.then check "#recaptcha-anchor > div.recaptcha-checkbox-border" I'm not a robot.and then click on "Download".

            attachments_data.external_url = page_main.find_element(By.ID, '#enviarDetalhesRecaptcha').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.licitacoes-e.com.br"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,41):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tCompradores"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tCompradores"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tCompradores"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tCompradores"]/tbody/tr'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)