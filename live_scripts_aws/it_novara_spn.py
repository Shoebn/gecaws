from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_novara_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
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
SCRIPT_NAME = "it_novara_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_novara_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)


    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
    #This script have 2 formats..
    # format-1) after opening the url click on this "Avvisi pubblici in corso".     "Tipologia" is unique keyword in format-1.
    try:
        notice_data.local_title = tender_html_element.text.split("Titolo :")[1].split("\n")[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.text.split('Data pubblicazione')[1].split("\n")[0].strip()
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.text.split('Data scadenza')[1].split("\n")[0].strip()
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a.bkg.detail-very-big').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bkg.table').get_attribute("href")                     
        fn.load_page(page_details1,notice_url,80)
    except Exception as e:
        logging.info("Exception in page_details1: {}".format(type(e).__name__))
           
    try:
        notice_data.notice_no = tender_html_element.text.split('Riferimento procedura :')[1].split("\n")[0].strip()
        if notice_data.notice_no == '':
            notice_data.notice_no = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CIG")]//following::td[18]').text
            if notice_data.notice_no == '':
                notice_data.notice_no = notice_data.notice_url.split("codice=")[1].split("&")[0].strip()
    except:
        try:
            notice_data.notice_no = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CIG")]//following::td[18]').text
            if notice_data.notice_no == '':
                notice_data.notice_no = notice_data.notice_url.split("codice=")[1].split("&")[0].strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    # Onsite Field -None
    # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Altri documenti')]" in page_details."main > div > div" use this selector for notice_text.
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    try:
        notice_text = page_details.find_element(By.CSS_SELECTOR, 'main > div > div').text
    except:
        pass
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> URL DI PUBBLICAZIONE SU WWW.SERVIZIOCONTRATTIPUBBLICI.IT
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get additional_tender_url.
    if url == urls[0]:
        try:
            attch_url = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div:nth-child(8) > ul > li > a').get_attribute("href")                     
            fn.load_page(page_details2,attch_url,80)
        except Exception as e:
            logging.info("Exception in page_details2: {}".format(type(e).__name__))

        try:
            notice_contract_type = tender_html_element.text.split("Avviso per :")[1].split("\n")[0].strip()
            if 'Servizi' in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            elif 'Lavori' in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            elif 'forniture' in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            else:
                pass
            notice_data.contract_type_actual = notice_contract_type
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass
        
        try:
            notice_data.additional_tender_url = page_details1.find_element(By.XPATH, '//*[contains(text(),"URL di Pubblicazione su www.serviziocontrattipubblici.it")]//following::td[17]').text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass
        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = 'COMUNE DI NOVARA'
            customer_details_data.org_parent_id = '1335742'
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            try:
                customer_details_data.contact_person = notice_text.split("RUP :")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> TIPO DI AMMINISTRAZIONE
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.
            try:
                customer_details_data.type_of_authority_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> COMUNE SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_city.
            try:
                customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> INDIRIZZO SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_address.
            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara")]//following::td[7]').text
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
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
                file_name = single_record.text
                if file_name != '':
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.text.strip()

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    
        try:
            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
                file_name = single_record.text
                if file_name != '':
                    attachments_data = attachments()
            
                    attachments_data.file_name = single_record.text

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except:
            try:
                for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'a.bkg.download'):
                    file_name = single_record.text
                    if file_name != '':
                        attachments_data = attachments()
  
                        attachments_data.file_name = single_record.text

                        attachments_data.external_url = single_record.get_attribute('href')

                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
                pass

    # Onsite Field -None
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get cpv_details.
        try:              
            cpvs_data = cpvs()
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> CODICE CPV
        # Onsite Comment -None
            try:
                cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
                cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
                notice_data.cpv_at_source = cpvs_data.cpv_code
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass

        try:
            Senza_Importo = page_details1.find_element(By.XPATH, '//*[contains(text(),"Senza Importo")]//following::td[8]').text
            est_amount = page_details1.find_element(By.XPATH, '//*[contains(text(),"Valore Importo a base asta")]//following::td[9]').text
            est_amount = re.sub("[^\d\.\,]","",est_amount).replace('.','').replace(',','.').strip()
            notice_data.est_amount =float(est_amount)
            if 'SI' in Senza_Importo:
                notice_data.netbudgetlc = notice_data.est_amount
                notice_data.netbudgeteuro = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount1: {}".format(type(e).__name__))
            pass

    #format-2)after opening the url click on this "Gare e procedure in corso".      "Stato" is the unique keyword in format-2.      in this format currently there is no tenders availabel so you have to refer the tender in following clicks "Gare e procedure scadute". 
    if url == urls[1]:
        try:
            notice_data.type_of_procedure_actual = notice_text.split("Procedura di gara :")[1].split("\n")[0].strip()
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/it_novara_spn_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass
    # Onsite Field -Tipologia appalto
    # Onsite Comment -1.split after "Tipologia appalto"	2)Repleace following keywords with given keywords("Lavori=Works","Servizi=Service")
        try:
            notice_contract_type = tender_html_element.text.split('Tipologia appalto :')[1].split("\n")[0].strip()
            if 'Servizi' in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            if 'Lavori' in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        try:
            notice_data.contract_type_actual = notice_contract_type
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
            pass
        # Onsite Field -Stato
        # Onsite Comment -1.split after "Stato"
        try:
            notice_data.document_type_description = tender_html_element.text.split("Stato :")[1].split("\n")[0].strip()
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
        # Onsite Field -None
        # Onsite Comment -add also this clicks in notice_text:1)click on "div.list-action > a.bkg.table" in tender_html_element."main > div > div" use this selector for notice_text. 2)click on "//*[contains(text(),'Lotti')]//following::a[1]" this two clicks in page_details."main > div > div" use this selector for notice_text.
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'main > div > div').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 

        # Onsite Field -Categoria/Prestazione
        # Onsite Comment -1.split after "Categoria/Prestazione :" 	Note:Click "div:nth-child(14) > ul > li > a" on page_detail then grab the data 	reference_url=https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_scaduti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/viewLotti.action&currentFrame=7&codice=G06924&ext=&_csrf=C2C0M0OX4SPM6100WY41AP63U2LFBJ6I
        try:
            lotti_url = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[4]/div[13]/ul/li/a').get_attribute("href")                     
            fn.load_page(page_details3,lotti_url,80)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            
        try:
            page_detail_text = page_details.find_element(By.CSS_SELECTOR, 'main > div > div').text
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

        try:
            page_detail3_text = page_details3.find_element(By.CSS_SELECTOR, 'main > div > div').text
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

        try:
            categories = page_detail3_text.split("Categoria/Prestazione :")
            for category in categories[1:]:
                category = category.split("\n")[0].strip()
                notice_data.category += category
        except:
            pass
    # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> URL DI PUBBLICAZIONE SU WWW.SERVIZIOCONTRATTIPUBBLICI.IT
    # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get additional_tender_url.

        try:
            notice_data.additional_tender_url = page_details1.find_element(By.XPATH, '//*[contains(text(),"URL di Pubblicazione su www.serviziocontrattipubblici.it")]//following::td[17]').text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass

        try:              
            cpvs_data = cpvs()
            try:
                cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
                cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
                notice_data.cpv_at_source = cpvs_data.cpv_code 
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__))
            pass

        try:
            est_amount = tender_html_element.text.split("Importo :")[1].split('\n')[0]
            est_amount = re.sub("[^\d\.\,]","",est_amount).replace('.','').replace(',','.').strip()
            notice_data.est_amount = float(est_amount)
            notice_data.netbudgetlc = notice_data.est_amount
            notice_data.netbudgeteuro = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount2: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            customer_details_data.org_name = 'COMUNE DI NOVARA'
            customer_details_data.org_parent_id = '1335742'

            try:
                customer_details_data.contact_person = page_detail_text.split("RUP :")[1].split("\n")[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> TIPO DI AMMINISTRAZIONE
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get type_of_authority_code.
            try:
                customer_details_data.type_of_authority_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione")]//following::td[4]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass

        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> COMUNE SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_city.

            try:
                customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"Comune Sede di Gara")]//following::td[6]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

        # Onsite Field -TABELLA INFORMATIVA D'INDICIZZAZIONE PER: BANDI, ESITI ED AVVISI >> INDIRIZZO SEDE DI GARA
        # Onsite Comment -click on "div.list-action > a.bkg.table" in tender_html_element to get org_address.

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara")]//following::td[7]').text
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
            lotti = page_details3.find_element(By.CSS_SELECTOR, 'main > div > div').text
            lot_details_data = lot_details()
            lot_details_data.lot_number = 1
   
            try:
                lot_details_data.lot_actual_number = lotti.split("CIG :")[1].split("-")[0].strip()
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            except:
                pass
            
            try:
                lot_cpv_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Codice CPV")]//following::td[15]').text
                lot_details_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]
                lot_details_data.lot_cpv_at_source = lot_details_data.lot_cpv_code 
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_title = lotti.split('Titolo :')[1].split("- CIG :")[0].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            try:
                lot_netbudget_lc  = lotti.split("Importo a base di gara :")[1].split("\n")[0]
                lot_netbudget_lc  = re.sub("[^\d\.\,]","",lot_netbudget_lc)
                lot_details_data.lot_netbudget_lc =float(lot_netbudget_lc.replace('.','').replace(',','.').strip())
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

        # Onsite Field -Importo a base di gara : 
        # Onsite Comment -1.split after "Importo a base di gara : ".

            try:
                lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass

        # Onsite Field -Tipologia appalto :
        # Onsite Comment -1)split after "Tipologia appalto :".	2)Replace follwing keywords with given respective kywords ('Servizi = Service','Lavori = Works ','forniture = Supply','Altro = pass none')

            try:
                contract_type = tender_html_element.text.split('Tipologia appalto :')[1].split("\n")[0].strip()
                if 'Servizi' in contract_type:
                    lot_details_data.contract_type = 'Service'
                if 'Lavori' in contract_type:
                    lot_details_data.contract_type = 'Works'
                if 'forniture' in contract_type:
                    lot_details_data.contract_type = 'Supply'
                lot_details_data.lot_contract_type_actual = contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
        
        try:
            attch_url = page_details.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div/div[4]/div[14]/ul/li/a').get_attribute("href")                     
            fn.load_page(page_details4,attch_url,80)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
        
    # Onsite Field -None
    # Onsite Comment -reference_url:"https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_scaduti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Bandi/view.action&currentFrame=7&codice=G05811&_csrf=F0S78CH40BAI1POTL7NMWXAXKEQVEU75".
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
                file_name = single_record.text
                if file_name != '':
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.text.strip()

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.bkg.download'):
                file_name = single_record.text
                if file_name != '':
                    attachments_data = attachments()
 
                    attachments_data.file_name = single_record.text.strip()
 
                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
         
        try:
            for single_record in page_details4.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
                file_name = single_record.text
                if file_name != '':
                    attachments_data = attachments()

                    attachments_data.file_name = single_record.text

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except:
            try:  
                for single_record in page_details4.find_elements(By.CSS_SELECTOR, 'a.bkg.download'):
                    file_name = single_record.text
                    if file_name != '':
                        attachments_data = attachments()

                        attachments_data.file_name = single_record.text

                        attachments_data.external_url = single_record.get_attribute('href')

                        attachments_data.attachments_cleanup()
                        notice_data.attachments.append(attachments_data)
            except Exception as e:
                logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_details2 = fn.init_chrome_driver(arguments) 
page_details3 = fn.init_chrome_driver(arguments) 
page_details4 = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_avvisi_lista.wp?_csrf=P9LAICEYB3R6UL2JAQRJTU67H4RZEU7E','https://llpp.comune.novara.it/PortaleAppalti/it/ppgare_bandi_lista.wp?_csrf=2GK4JJ0896F537EU2R9ITE17DDG3U496'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(1,4):
            try:
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'div.list-item')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input.nav-button.nav-button-right')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.list-item'),page_check))
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
    page_details1.quit()
    page_details2.quit()
    page_details3.quit()
    page_details4.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
