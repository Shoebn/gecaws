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
SCRIPT_NAME = "it_novara_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_novara_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4



#This script have 2 formats..
# format-1) after opening the url click on this "Avvisi pubblici in corso".     "Tipologia" is unique keyword in format-1.

    # Onsite Field -Tipologia :
    # Onsite Comment -1.split after "Tipologia :".
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(2)").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_novara_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Titolo :
    # Onsite Comment -1.split after "Titolo :"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avviso per :
    # Onsite Comment -1.split after "Avviso per : ".	2)Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply','Altro = pass none')

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Avviso per :
    # Onsite Comment -1.split after "Avviso per : ".

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione :
    # Onsite Comment -1.split after "Data pubblicazione :".

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
    # Onsite Comment -1.split after "Data scadenza :".	2.if notice_deadline is not present then take thrshold.

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -1.split after "Riferimento procedura : ".

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -1.split notice_no from notice_url. eg., here "https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00253&_csrf=BVVDSS0QMBLATUMGGLJ1MCTPRGGS7PAA" take only "A00253" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -1.click on notice_url	2.split after "Riferimento procedura :".

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimento procedura :")]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Altri documenti')]" in page_details."main > div > div" use this selector for notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> URL DI PUBBLICAZIONE SU WWW.SERVIZIOCONTRATTIPUBBLICI.IT
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get additional_tender_url.

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"URL di Pubblicazione su www.serviziocontrattipubblici.it")]//following::td[17]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.portgare-view >  div:nth-child(4)'):
            customer_details_data = customer_details()
        # Onsite Field -Stazione appaltante :
        # Onsite Comment -1.split after "Stazione appaltante :".

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
        # Onsite Field -Responsabile unico procedimento :
        # Onsite Comment -1.split after "Responsabile unico procedimento :".

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> TIPO DI AMMINISTRAZIONE
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> COMUNE SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_city.

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> INDIRIZZO SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_address.

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara")]//following::td[7]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -ref_url:"https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00241&_csrf=FDQN1QPEQUB0FWQRCWUIXOGSWC811HR3"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            attachments_data = attachments()
        # Onsite Field -Documentazione
        # Onsite Comment -1.take in text format.

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Documentazione")]//following::div/ul/li/a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Documentazione")]//following::div/ul/li/a[1]').get_attribute('href')
            
        
        # Onsite Field -Comunicazioni della stazione appaltante
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul li > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Comunicazioni della stazione appaltante
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Comunicazioni della stazione appaltante")]//following::ul/li/a').get_attribute('href')
            
        

#click on "//*[contains(text(),'Altri documenti')]" in page_details to get this attchments_details.     ref_url:https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/viewAltriDocumenti.action&currentFrame=7&codice=A00253&ext=&_csrf=AZN1O2FA53VX7G6HC1I8WEUI304STCA2
        # Onsite Field -Documenti
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul > li').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documenti
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul > li > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

# Onsite Field -None
# Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get cpv_details.

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            cpvs_data = cpvs()
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
        # Onsite Comment -None

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_codes_at_source = 'CPV'


    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
    # Onsite Comment -
    try:
        notice_data.est_amount = page_details.find_element(By.Xpath, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass



#if "//*[contains(text(),"Senza Importo")]//following::td[8]" in this field "SI" is given then take the amount under "VALORE IMPORTO A BASE ASTA" field grab in netbudgetlc and netbudgeteuro.  and
#if "//*[contains(text(),"Senza Importo")]//following::td[8]" in this field "NO" is given then take the amount under "VALORE IMPORTO A BASE ASTA" field grab in grossbudgetlc and grossbudgeteuro.

    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
    # Onsite Comment -if "SENZA IMPORTO" under this field "NO" is given then only grab the amount.
    try:
        notice_data.grossbudgetlc = page_details.find_element(By.Xpath, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass


    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
    # Onsite Comment -if "SENZA IMPORTO" under this field "NO" is given then only grab the amount.
    try:
        notice_data.grossbudgeteuro = page_details.find_element(By.Xpath, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
    except Exception as e:
        logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
        pass


    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
    # Onsite Comment -if "SENZA IMPORTO" under this field "SI" is given then only grab the amount.
    try:
        notice_data.netbudgetlc = page_details.find_element(By.Xpath, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass


    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA 
    # Onsite Comment -if "SENZA IMPORTO" under this field "SI" is given then only grab the amount.
    try:
        notice_data.netbudgeteuro = page_details.find_element(By.Xpath, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass





#format-2)after opening the url click on this "Gare e procedure in corso".      "Stato" is the unique keyword in format-2.      in this format currently there is no tenders availabel so you have to refer the tender in following clicks "Gare e procedure scadute".
    
    # Onsite Field -Riferimento procedura
    # Onsite Comment -1.split after "Riferimento procedura".

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -1.split notice_no from notice_url. eg., here "https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Avvisi/view.action&currentFrame=7&codice=A00253&_csrf=BVVDSS0QMBLATUMGGLJ1MCTPRGGS7PAA" take only "A00253" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Riferimento procedura :
    # Onsite Comment -1.click on notice_url	2.split after "Riferimento procedura :".

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimento procedura :")]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione
    # Onsite Comment -1.split after "Data pubblicazione"

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
    
    # Onsite Field -Data scadenza
    # Onsite Comment -1.split after "Data scadenza".

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "form > div > div:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto
    # Onsite Comment -1.split after "Tipologia appalto"	2)Repleace following keywords with given keywords("Lavori=Works","Servizi=Service")

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto
    # Onsite Comment -1.split after "Tipologia appalto".

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Stato
    # Onsite Comment -1.split after "Stato"

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Categoria/Prestazione
    # Onsite Comment -1.split after "Categoria/Prestazione :" 	Note:Click "div:nth-child(14) > ul > li > a" on page_detail then grab the data 	reference_url=https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_scaduti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/viewLotti.action&currentFrame=7&codice=G06924&ext=&_csrf=C2C0M0OX4SPM6100WY41AP63U2LFBJ6I

    try:
        notice_data.category = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-subrow  div > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Visualizza scheda
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Lotti')]//following::a[1]" this two clicks in page_details."main > div > div" use this selector for notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> URL DI PUBBLICAZIONE SU WWW.SERVIZIOCONTRATTIPUBBLICI.IT
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get additional_tender_url.

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"URL di Pubblicazione su www.serviziocontrattipubblici.it")]//following::td[17]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_codes_at_source = 'CPV'
    
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get lot_cpv_details.

    try:
        notice_data.cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            cpvs_data = cpvs()
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get cpv_details.

            try:
                cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo : 
    # Onsite Comment -1.split after "Importo : ".
    try:
        notice_data.est_amount = page_details1.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo : 
    # Onsite Comment -1.split after "Importo : ".
    try:
        notice_data.grossbudgetlc = page_details1.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Importo : 
    # Onsite Comment -1.split after "Importo : ".
    try:
        notice_data.grossbudgeteuro = page_details1.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in grossbudgeteuro: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.portgare-view >  div:nth-child(4)'):
            customer_details_data = customer_details()
        # Onsite Field -Stazione appaltante
        # Onsite Comment -1.split after "Stazione appaltante".

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
        # Onsite Field -None
        # Onsite Comment -1.split after "RUP:"

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[3]/div[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> TIPO DI AMMINISTRAZIONE
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> COMUNE SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_city.

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> INDIRIZZO SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_address.

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara")]//following::td[7]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    


# Onsite Field -None
# Onsite Comment -click on "//*[contains(text(),'Lotti')]//following::a[1]" in page_details to take lot_details.
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            lot_details_data = lot_details()
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "CIG :".

            try:
                lot_details_data.lot_actual_number = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Titolo :
        # Onsite Comment -1.split after "Titolo :".

            try:
                lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass



        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

            try:
                lot_details_data.lot_grossbudget_lc = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

            try:
                lot_details_data.lot_grossbudget = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipologia appalto :
        # Onsite Comment -split after "Tipologia appalto :"

            try:
                lot_details_data.lot_contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tipologia appalto :
        # Onsite Comment -1)split after "Tipologia appalto :".	2)Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply','Altro = pass none')

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
        

    
# Onsite Field -None
# Onsite Comment -reference_url:"https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_scaduti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/view.action&currentFrame=7&codice=G05811&_csrf=F0S78CH40BAI1POTL7NMWXAXKEQVEU75".

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            attachments_data = attachments()
        # Onsite Field -Documentazione
        # Onsite Comment -1.take in text format.

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(6) > div > div > ul > li > a').get_attribute('href')
            
        
        # Onsite Field -Documentazione richiesta ai concorrenti
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(7) > div > div > ul > li > div > span').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documentazione richiesta ai concorrenti
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(7) > div > div > ul > li > div > span > a').get_attribute('href')
            
        
        # Onsite Field -Comunicazioni della stazione appaltante
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul >li > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Comunicazioni della stazione appaltante
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul >li  > ul >li > a').get_attribute('href')
            
        


#click on "//*[contains(text(),'Altri atti e documenti')]" in page_details to get this attchments_details.   ref-url:"https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_scaduti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/viewAttiDocumenti.action&currentFrame=7&codice=G05811&ext=&_csrf=6OOVWDK8P25TYW2TT439N5E57LQMU2E8"        
        # Onsite Field -Documenti
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul > li').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Documenti
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section > div > ul > li > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?_csrf=P9LAICEYB3R6UL2JAQRJTU67H4RZEU7E"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
