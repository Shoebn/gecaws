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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_bari"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    
    notice_data = tender()
    
    notice_data.script_name = 'it_bari'
    
    notice_data.main_language = 'IT'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form:nth-child(4) div  div:nth-child(2)').text.split(":")[1]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form:nth-child(4) > div div:nth-child(7)').text.split(":")[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'form:nth-child(4) div  div:nth-child(3)').text.split(":")[1]
        if "Servizi" in notice_data.notice_contract_type:
            notice_data.notice_contract_type="Service"
        elif "Lavori" in notice_data.notice_contract_type:
            notice_data.notice_contract_type='Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.document_type_description = "Gare e procedure in corso"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'form:nth-child(4) div div:nth-child(2)').text.split(":")[1]
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'form:nth-child(4) > div div:nth-child(4)').text.split(":")[1].split("€")[0]
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form:nth-child(4) > div div:nth-child(5)").text.split(":")[1]
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "form:nth-child(4) > div div:nth-child(6)").text.split(":")[1]
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline_time = notice_deadline.split("by")[1]
        notice_deadline_date= re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_deadline_time = re.findall('\d{2}.\d{2}',notice_deadline_time)[0]
        notice_deadline_concat = notice_deadline_date+' '+notice_deadline_time
        notice_data.notice_deadline = datetime.strptime(notice_deadline_concat,'%d/%m/%Y %H.%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.column.content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.column.content > div > div:nth-child(5)'):
            custom_tags_data = custom_tags()
            custom_tags_data.tender_custom_tag_description = single_record.find_element(By.CSS_SELECTOR, 'div.column.content > div > div:nth-child(5) > div:nth-child(5)').text.split(":")[1]
            custom_tags_data.custom_tags_cleanup()
            notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form:nth-child(4) > div div:nth-child(1)').text.split(":")[1]
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.first-detail-section > div:nth-child(3)').text.split("Responsabile unico procedimento : ")[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '  div.column.content > div > div:nth-child(6) > div > div > ul li '):
            attachments_data = attachments()
            attachments_data.file_type = 'pdf'
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.type_of_procedure = page_details.find_element(By.CSS_SELECTOR, 'div.column.content > div div div:nth-child(4)').text.split(":")[1]
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass
    
    try:
        url1= page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(11) > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details1,url1,80)
    except:
        pass
    
 
    try: 
        lot_number=1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.detail-section'):
            lot_details_data = lot_details() 
            lot_details_data.lot_number = lot_number
            lot_details_data.contract_type = notice_data.notice_contract_type
        
            try:
                lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split(":")[1]
                lot_details_data.lot_description= GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                if 'Lotto' in single_record.text:
                    lot_title = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text.split(":")[1]
                    lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
                else:
                    lot_details_data.lot_title = notice_data.notice_title

            except:
                lot_details_data.lot_title = notice_data.notice_title
        
            try:
                lot_grossbudget = single_record.find_element(By.XPATH, '//*[@id="ext-container"]/div[7]/div/div[1]/div/div/div[2]').text.split(":")[1].split("€")[0].strip()
                lot_grossbudget = re.sub("[^\d\.\,]", "", lot_grossbudget)
                lot_details_data.lot_grossbudget = float(lot_grossbudget.replace('.','').replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
            
            try:
                notice_summary_english = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > div:nth-child(1)').text.split(":")[1]
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass
               
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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

type_of_procedure_actual 
    # Onsite Field -Procedura di gara :
    # Onsite Comment -1.split the data after "Procedura di gara :" field	2."01-PROCEDURA APERTA" here take "PROCEDURA APERTA" in type_of_procedure_actual.
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),"Procedura di gara : ")]").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_novara_spn_procedure",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass


tender cpv 
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
    notice_data.class_at_source = 'CPV'




lot details 
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
            lot_details_data = lot_details()
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CIG
        # Onsite Comment -1.click on "div.list-action > a.bkg.table" in tender_html_element to get lot_actual_no.

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CIG")]//following::td[18]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split after "Titolo :".

            try:
                lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Bando di gara")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
#cmt for the fields -lot_grossbudget_lc,lot_grossbudget,lot_netbudget,lot_netbudget_lc.
#if "//*[contains(text(),"Senza Importo")]//following::td[8]" in this field "SI" is given then take the amount under "VALORE IMPORTO A BASE ASTA" field grab in lot_netbudget_lc and lot_netbudget.  and
#if "//*[contains(text(),"Senza Importo")]//following::td[8]" in this field "NO" is given then take the amount under "VALORE IMPORTO A BASE ASTA" field grab in lot_grossbudget_lc and lot_grossbudget.
    
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
        # Onsite Comment -if "SENZA IMPORTO" under this field "NO" is given then only grab the amount.
            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
        # Onsite Comment -if "SENZA IMPORTO" under this field "NO" is given then only grab the amount.

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.XPATH, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
        # Onsite Comment -if "SENZA IMPORTO" under this field "SI" is given then only grab the amount.

            try:
                lot_details_data.lot_netbudget = page_details.find_element(By.XPATH, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> VALORE IMPORTO A BASE ASTA
        # Onsite Comment -if "SENZA IMPORTO" under this field "SI" is given then only grab the amount.

            try:
                lot_details_data.lot_netbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass


        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CONTRATTO
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get contract_type_actual.

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contratto")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CONTRATTO
        # Onsite Comment -1)click on "div.list-action > a.bkg.table" in tender_html_element to get org_city.	2)Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply','Altro = pass none')

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Contratto")]//following::td[2]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        

        # Onsite Field -None
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get lot_cpv_details.
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'main > div > div'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
                    # Onsite Comment -None

                    lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    




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

            attachments_data.external_url = page_details.find_element(By.CS                                                                                                                                                                                                                                                                                                                                             attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass    
  
  


    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.portgare-view >  div:nth-child(4)'):
            customer_details_data = customer_details()

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


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://portaleappalti.comune.bari.it/PortaleAppalti/it/ppgare_bandi_lista.wp;jsessionid=D109CF0A30A2F7A7F795258C61895E38?_csrf=FR8HGMUYM22N3QRW09DBD627XLR34X1D'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,9):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break


            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
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
