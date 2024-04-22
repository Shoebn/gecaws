from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_unirc"
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
SCRIPT_NAME = "it_unirc"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global bidder_name1
    notice_data = tender()
    
    notice_data.script_name = 'it_unirc'
    notice_data.main_language = 'IT'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if the notice text have keyword like "Partecipanti" and "Aggiudicatari" then the notice type will be 7 
    
    # Onsite Field -Avvisi e bandi di gara - Profilo di committente
    # Onsite Comment -None

    try:                                                                                     
        notice_data.document_type_description = tender_html_element.find_element(By.XPATH, '//*[@id="regola_default"]/div[1]/div/section/h3/span ').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -OGGETTO
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DATA DI PUBBLICAZIONE
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if notice_data.notice_no == '':
            try:
                notice_data.notice_no = re.findall('\d+_\d+',notice_data.notice_url)[0]
            except:
                pass
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.review36').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Data di scadenza: ')]//following::strong[1]").text
        notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedura di scelta del contraente:
    # Onsite Comment -take only "Procedura di scelta del contraente:" from the given selector

    try:
        notice_text  = page_details.find_element(By.CSS_SELECTOR, 'div.review36').text
        if 'Procedura di scelta del contraente:' in notice_text:
            notice_data.type_of_procedure_actual = notice_text.split("Procedura di scelta del contraente: ")[1].split("\n")[0]
            if "05-DIALOGO COMPETITIVO" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "Competitive dialogue"
            elif "37-PROCEDURA COMPETITIVA CON NEGOZIAZIONE" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "Competitive tendering"
            elif "17-AFFIDAMENTO DIRETTO EX ART. 5 DELLA LEGGE 381/9" in notice_data.type_of_procedure_actual or "23-AFFIDAMENTO DIRETTO" in notice_data.type_of_procedure_actual or "24-AFFIDAMENTO DIRETTO A SOCIETA' IN HOUSE" in notice_data.notice_data.type_of_procedure_actual or "25-AFFIDAMENTO DIRETTO A SOCIETA' RAGGRUPPATE" in notice_data.type_of_procedure_actual or "CONSORZIATE O CONTROLLATE NELLE CONCESSIONI E NEI PARTENARIATI" in notice_data.type_of_procedure_actual or "26-AFFIDAMENTO DIRETTO IN ADESIONE AD ACCORDO QUADRO" in notice_data.type_of_procedure_actual or "CONVENZIONE" in notice_data.type_of_procedure_actual or "31-AFFIDAMENTO DIRETTO PER VARIANTE SUPERIORE AL 20% DELL'IMPORTO CONTRATTUALE" in notice_data.type_of_procedure_actual or  "36-AFFIDAMENTO DIRETTO PER LAVORI SERVIZI O FORNITURE SUPPLEMENTARI" in notice_data.type_of_procedure_actual or  "39-AFFIDAMENTO DIRETTO PER MODIFICHE CONTRATTUALI O VARIANTI PER LE QUALI È NECESSARIA UNA NUOVA PROCEDURA DI AFFIDAMENTO" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure ="Direct award"
            elif "33-PROCEDURA NEGOZIATA PER AFFIDAMENTI SOTTO SOGLIA" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "Negotiated procedure -"
            elif "03-PROCEDURA NEGOZIATA PREVIA PUBBLICAZIONE" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "competitive with negotiation"
            elif "04-PROCEDURA NEGOZIATA SENZA PREVIA PUBBLICAZIONE" in notice_data.type_of_procedure_actual or  "06-PROCEDURA NEGOZIATA SENZA PREVIA INDIZIONE DI GARA (SETTORI SPECIALI)" in notice_data.type_of_procedure_actual or "22-PROCEDURA NEGOZIATA CON PREVIA INDIZIONE DI GARA (SETTORI SPECIALI)" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "Negotiated without prior call for competition"
            elif "01-PROCEDURA APERTA" in  notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "Open"
            elif "07-SISTEMA DINAMICO DI ACQUISIZIONE" in notice_data.type_of_procedure_actual or "08-AFFIDAMENTO IN ECONOMIA - COTTIMO FIDUCIARIO" in notice_data.type_of_procedure_actual or "14-PROCEDURA SELETTIVA EX ART 238 C.7 D.LGS. 163/2006" in notice_data.type_of_procedure_actual or "27-CONFRONTO COMPETITIVO IN ADESIONE AD ACCORDO QUADRO" in notice_data.type_of_procedure_actual or "CONVENZIONE" in notice_data.type_of_procedure_actual or "28-PROCEDURA AI SENSI DEI REGOLAMENTI DEGLI ORGANI COSTITUZIONALI" in notice_data.type_of_procedure_actual or "32-AFFIDAMENTO RISERVATO'>32-AFFIDAMENTO RISERVATO" in notice_data.type_of_procedure_actual or "34-PROCEDURA ART.16 COMMA 2-BIS DPR 380" in notice_data.type_of_procedure_actual or "2001 PER OPERE URBANIZZAZIONE A SCOMPUTO PRIMARIE SOTTO SOGLIA COMUNITARIA" in notice_data.type_of_procedure_actual or "38-PROCEDURA DISCIPLINATA DA REGOLAMENTO INTERNO PER SETTORI SPECIALI" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = "Other"        
            elif "02-PROCEDURA RISTRETTA" in notice_data.type_of_procedure_actual or "21-PROCEDURA RISTRETTA DERIVANTE DA AVVISI CON CUI SI INDICE LA GARA" in notice_data.type_of_procedure_actual or "29-PROCEDURA RISTRETTA SEMPLIFICATA" in notice_data.type_of_procedure_actual or "30-PROCEDURA DERIVANTE DA LEGGE REGIONALE" in notice_data.type_of_procedure_actual:
                notice_data.type_of_procedure = 'Restricted" -'
            else:
                notice_data.type_of_procedure = "Other"
        else:
            pass
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo dell'appalto:
    # Onsite Comment -None

    try:
        grossbudgetlc = notice_text.split("Importo delle somme liquidate: €")[1].split("\n")[0]
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        grossbudgetlc = grossbudgetlc.replace('.','').replace(',','.').strip()
        notice_data.grossbudgetlc = float(grossbudgetlc)
        notice_data.est_amount = float(grossbudgetlc)
    except Exception as e:
        logging.info("Exception in notice_data grossbudgetlc: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_url1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > div > a').get_attribute("href")
        fn.load_page(page_details1,notice_url1,80)
        try:
            notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-sm-12.contenutoCentrale').get_attribute("outerHTML")                     
        except Exception as e:
            logging.info("Exception in notice_text: {}".format(type(e).__name__))
            pass
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#reviewOggetto > div > div'):
            customer_details_data = customer_details()
            
            customer_details_data.org_name = 'Università Mediterranea di Reggio Calabria'
            customer_details_data.org_parent_id = '7797294'
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            
        # Onsite Field -STRUTTURA COMPETENTE
        # Onsite Comment -None

            try:
                customer_details_data.org_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
            
    
        # Onsite Field -Indirizzo:
        # Onsite Comment -take org_address from page detail1 the selector for page detail1 : td:nth-child(3) > div > a (STRUTTURA COMPETENTE)

            try:
                org_address = single_record.text
                if 'Indirizzo' in org_address:
                    customer_details_data.org_address = org_address.split('Indirizzo:')[1].split('\n')[0].strip()
                else:
                    pass
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -RUP:/Responsabile:
        # Onsite Comment -if "RUP:" is not available den take "Responsabile:" (//*[contains(text(),'Responsabile:')]//following::a[1])  from page detail1 (td:nth-child(3) > div > a) as contact_person

            try:
                contact_person = single_record.text
                if 'Responsabile:' in contact_person:
                    customer_details_data.contact_person = contact_person.split('Responsabile:')[1].split('\n')[0]
                elif 'RUP:' in contact_person:
                    
                    customer_details_data.contact_person = contact_person.split('RUP:')[1].split('\n')[0]
                else:
                    pass
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
                
        
        # Onsite Field -Telefono:
        # Onsite Comment -take org_phone from page detail1 the selector for page detail1 : td:nth-child(3) > div > a (STRUTTURA COMPETENTE)

            try:
                org_phone = page_details1.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div > div.campoOggetto114').text
                if 'Telefono:' in org_phone:
                    customer_details_data.org_phone = org_phone.split(':')[1]
                else:
                    pass
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email:
        # Onsite Comment -take org_email  from page detail1 the selector for page detail1 : td:nth-child(3) > div > a (STRUTTURA COMPETENTE)

            try:
                org_email = single_record.text
                if 'Email:' in org_email:
                    customer_details_data.org_email = page_details1.find_element(By.XPATH, "//*[contains(text(),'Email:')]//following::a[1]").text
                else:
                    pass
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Fax:
        # Onsite Comment -take org_fax from page detail1 the selector for page detail1 : td:nth-child(3) > div > a (STRUTTURA COMPETENTE)

            try:
                org_fax = single_record.text
                if 'Fax:' in org_fax:
                    customer_details_data.org_fax = org_fax.split('Fax:')[1].split('\n')[0]
                else:
                    pass
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except:
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Università Mediterranea di Reggio Calabria'
        customer_details_data.org_parent_id = '7797294'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    
    try:
        single_record  = page_details.find_element(By.CSS_SELECTOR, 'div.review36').text
        if 'Aggiudicatari' in single_record:
            bidder_name1 = page_details.find_element(By.CSS_SELECTOR, 'ul.div_partecipanti > li').text
        else:
            bidder_url = page_details.find_element(By.CSS_SELECTOR, '#reviewOggetto > div > div > div > ul > li > a').get_attribute("href")
            fn.load_page(page_details2,bidder_url,80)
            page_details2_data = page_details2.find_elements(By.CSS_SELECTOR, 'div.review36').text
            if 'Aggiudicatari' in page_details2_data:
                bidder_name1 = page_details2.find_element(By.CSS_SELECTOR, 'ul.div_partecipanti > li').text
            else:
                pass
        if 'Partecipanti' in single_record or 'Aggiudicatari' in single_record or 'Partecipanti' in page_details2_data or 'Aggiudicatari' in page_details2_data:
            notice_data.notice_type = 7
        else:
            notice_data.notice_type = 4
          
        if notice_data.notice_type == 7:
            lot_details_data = lot_details()
            # Onsite Field -OGGETTO
            # Onsite Comment -None
            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            try:
                single_record  = page_details.find_element(By.CSS_SELECTOR, 'div.review36').text
                award_details_data = award_details()
                award_details_data.bidder_name = bidder_name1
                try:
                    grossawardvaluelc = single_record
                    if 'aggiudicazione:' in grossawardvaluelc:
                        grossawardvaluelc = grossawardvaluelc.split("Importo di aggiudicazione:")[1].split("\n")[0]
                        grossawardvaluelc = re.sub("[^\d\.\,]", "",grossawardvaluelc)
                        grossawardvaluelc = grossawardvaluelc.replace('.','').replace(',','.').strip()
                        award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass

    # Onsite Field -Aggiudicatari
    # Onsite Comment -None

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Allegati
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()
        # Onsite Field -Allegati
        # Onsite Comment -split  file_type from Allegati
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'span').text.split(' - ')[3].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -split  file_name from Allegati

            try:
                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -split  file_size from Allegati

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split(' - ')[2].split(' - ')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -None

            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
        
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
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://unirc.portaleamministrazionetrasparente.it/index.php?id_sezione=876&id_cat=0'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'>successiva')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="regola_default"]/div[2]/div/section/div[2]/table/tbody/tr[2]'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
