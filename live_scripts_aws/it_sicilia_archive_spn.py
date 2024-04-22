from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_sicilia_archive_spn"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_sicilia_archive_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'it_sicilia_archive_spn'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    # Onsite Field -Titolo :
    # Onsite Comment -split the data after "Titolo :"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.replace('Titolo :','').strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -split the data after "Tipologia appalto :",  Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.replace('Tipologia appalto :','').strip()
        if notice_contract_type == 'Servizi':
            notice_data.notice_contract_type = 'Service'
        elif notice_contract_type == 'Lavori':
            notice_data.notice_contract_type = 'Works'
        elif notice_contract_type == 'forniture' or notice_contract_type == 'Forniture':
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -None
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.replace('Tipologia appalto :','').strip()
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo
    # Onsite Comment -split the data after "Importo "
    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text.split(':')[1].split('€')[0].replace('.','').replace(',','.')
        notice_data.netbudgetlc = float(grossbudgetlc)
        notice_data.netbudgeteuro = notice_data.netbudgetlc
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Data pubblicazione :
    # Onsite Comment -split the data after "Data pubblicazione :"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data scadenza :
    # Onsite Comment -split the data after " Data scadenza : "

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(6)").text
        notice_deadline1 = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_deadline2 = re.findall('\d+:\d+',notice_deadline)[0]
        notice_deadline = notice_deadline1 +" "+ notice_deadline2
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -split the data after "Riferimento procedura :"
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(7)').text.replace('Riferimento procedura :','')
        if notice_data.notice_no =='':
            notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'div.list-action > a.bkg.detail-very-big').get_attribute("href")
            code = re.search(r'codice=([A-Z0-9]+)', notice_no).group(1)
            notice_data.notice_no = code
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    # Onsite Field --Stato :
    # Onsite Comment -split the data after "Stato :"
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(8)').text.replace('Stato :','')
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Visualizza scheda
    # Onsite Comment -inspect the url for detail_page ref_url : "https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_bandi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/view.action&currentFrame=7&codice=G00607&_csrf=JXSLZAIAGTCO37T59REEPZA22LRM6D2K"
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.column.content > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Procedura di gara :
    # Onsite Comment -split the data after "Procedura di gara :" field
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Procedura di gara : ')]/..").text.replace('Procedura di gara : ','').strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_appalti_spn_procedure.CSV",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Denominazione :")]/..').text.replace('Denominazione :','')
        
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP :")]/..').text.replace('RUP :','')
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -Elenco lotti
    # Onsite Comment -in detail_page click on  "Lotti" (selector : "div:nth-child(14) > ul a") for lot_details1
    try:
        Lotti_url = page_details.find_element(By.XPATH,'//a[contains(text(),"Lotti")]').get_attribute("href")
        fn.load_page(page_details1, Lotti_url, 80)
        logging.info(Lotti_url)
        time.sleep(3)
    except Exception as e:
        logging.info("Exception in Lotti_url: {}".format(type(e).__name__))
        pass
    
    
    try:
        lot_number = 1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div .detail-section'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(2)').text.replace('Titolo :', '')
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)


            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            except:
                pass

            try:
                grossbudget = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(3)').text
                lot_grossbudget_lc = grossbudget.split(':')[1].split('€')[0].replace('.','').replace(',','.')
                lot_details_data.lot_netbudget_lc = float(lot_grossbudget_lc)
                lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
            except:
                pass
            try:
                lot_actual = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(2)').text
                if 'CIG :' in lot_actual:
                    cig_numbers = re.findall(r'CIG : ([A-Z0-9]+)', lot_actual)[0]
                    lot_details_data.lot_actual_number= cig_numbers
            except Exception as e:
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    # Onsite Field -None
    # Onsite Comment -documents are available in detail_page and detail_page_1
    try:
        # Onsite Field -Documentazione di gara
        # Onsite Comment -None
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(6)  ul > li a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            attachments_data.file_description = single_record.text
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
        # Onsite Field -Documentazione richiesta ai concorrenti
        # Onsite Comment -None
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div>ul > li> div > span a'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            attachments_data.file_description = single_record.text
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments1: {}".format(type(e).__name__))
        pass
    # Onsite Field -Documenti
    # Onsite Comment -in detail_page click on  "Altri atti e documenti" (selector :  "div:nth-child(15) > ul > li" ),  split only file_name for ex."Determina a contrarre (Pubblicato il 28/06/2023)" , here split only "Determina a contrarre" , ref_url : "https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_bandi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/viewAttiDocumenti.action&currentFrame=7&codice=G00605&ext=&_csrf=8Z4R4ZF2X5JIJLYK4ULOAGGMSX98XCWC"
    # Onsite Field -Documenti
    # Onsite Comment -in detail_page click on  "Altri atti e documenti" (selector :  "div:nth-child(15) > ul > li" ),  ref_url_of_detail_page_1 : "https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_bandi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/viewAttiDocumenti.action&currentFrame=7&codice=G00605&ext=&_csrf=8Z4R4ZF2X5JIJLYK4ULOAGGMSX98XCWC"
    try:
        page_details.find_element(By.XPATH,'//a[contains(text(),"Altri atti e documenti")]').click()
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'div.detail-section > div > ul > li'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'a').text
            attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR,'a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__))
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://appalti.regione.sicilia.it/PortaleAppalti/it/ppgare_bandi_lista.wp?_csrf=8C6D54AV1FEMR7DFDUI9ZILIQVW8MO84"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="list-item"]')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="list-item"]')))[records]
            extract_and_save_notice(tender_html_element)

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    page_details1.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
    