from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_starttoscana_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_starttoscana_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_starttoscana_spn'

    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2

    notice_data.notice_type = 4
    
    # Onsite Field -take publication date as threshold
    # Onsite Comment -None

    try:  
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    # Onsite Field -DESCRIZIONE
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -If keywords such as "Open procedure, OPEN PROCEDURE" , "Negotiated procedure" is given in title map it with the csv file
    # Onsite Comment -None
    try:
        type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "#table-lista-bandi td:nth-child(1)").text
        if 'Procedura aperta' in type_of_procedure_actual or 'Procedura negoziata' in type_of_procedure_actual or 'PROCEDURA APERTA' in type_of_procedure_actual or 'Procedura Negoziata' in type_of_procedure_actual:
            try:
                notice_data.type_of_procedure_actual = re.findall("Procedura negoziata",type_of_procedure_actual)[0]
            except:
                try:
                    notice_data.type_of_procedure_actual = re.findall("Procedura aperta",type_of_procedure_actual)[0]
                except:
                    notice_data.type_of_procedure_actual = re.findall("PROCEDURA APERTA",type_of_procedure_actual)[0]
            type_of_procedure1 = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            type_of_procedure = type_of_procedure1.strip()
            notice_data.type_of_procedure = fn.procedure_mapping("assets/it_starttoscana_spn_category.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DETTAGLIO
    # Onsite Comment -None
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.GR0_GridCol_Link > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Bando
    # Onsite Comment -also take notice_no from notice url
#
    try:  
        notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Bando')]").text.split("(")[1].split(")")[0]
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Invito')]").text.split("(")[1].split(")")[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Tipo Appalto:
    # Onsite Comment -"Servizi  = Srvice, Forniture = Supply, Lavori pubblici=Works"

    try:
        notice_contract_type = page_details.find_element(By.XPATH, "//*[contains(text(),'Tipo Appalto:')]//following::td[1]").text
        if 'Servizi' in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Forniture" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Lavori pubblici" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipo Appalto:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CIG:
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, "//*[contains(text(),'CIG:')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
       # Onsite Field -Importo Appalto:
    # Onsite Comment -None

    try:  
        est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Importo Appalto:')]//following::td[1]").text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgeteuro = notice_data.est_amount
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Incaricato:')]//following::td[1]").text
    except:
        pass

    
    try:
        attch = page_details.find_element(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(12) > td > table > tbody > tr')
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(12) > td > table > tbody > tr')[1:-1]:
            attachments_data = attachments()
        # Onsite Field -for key word "rettifica bando guue" in documents take notice type - "16"
        # Onsite Comment -ref url = "https://www.sanita.start.toscana.it/portalegare/index.php/bandi?getdettaglio=yes&bando=92874&tipobando=Bando&RicQ=YES&VisQ=SI&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-22T18:00:00&jk="
            
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(2)").click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
            if 'rettifica bando guue' in attachments_data.file_name:
                notice_data.notice_type = 16
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#template_doc > tbody > tr:nth-child(11) > td > table > tbody > tr')[1:-1]:
                attachments_data = attachments()
            # Onsite Field -for key word "rettifica bando guue" in documents take notice type - "16"
            # Onsite Comment -ref url = "https://www.sanita.start.toscana.it/portalegare/index.php/bandi?getdettaglio=yes&bando=92874&tipobando=Bando&RicQ=YES&VisQ=SI&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-22T18:00:00&jk="
                try:
                    attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.split(".")[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(2)").click()
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
                if 'rettifica bando guue' in attachments_data.file_name:
                    notice_data.notice_type = 16
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments1: {}".format(type(e).__name__)) 
            pass
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '//*[@id="div_rss_lista"]/div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

     # Onsite Field -Requisiti di Qualificazione:
    # Onsite Comment -None 
    
    try:
        click2 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Chiarimenti')]")))
        page_details.execute_script("arguments[0].click();",click2)
        time.sleep(5)
    except:
        pass

    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'td.CellGridPrintProducts.CellAllegato a'):
            data_text = single_record.text

        # Onsite Field -for key word "rettifica bando guue" in documents take notice type - "16"
        # Onsite Comment -ref url = "https://www.sanita.start.toscana.it/portalegare/index.php/bandi?getdettaglio=yes&bando=92874&tipobando=Bando&RicQ=YES&VisQ=SI&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-22T18:00:00&jk="
            if data_text !='':
                attachments_data = attachments()
                attachments_data.external_url = single_record.get_attribute("href")

                try:
                    attachments_data.file_type = single_record.text.split(".")[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass


                attachments_data.file_name = single_record.text.replace(attachments_data.file_type,'')
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments2: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        click3 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Esiti e Pubblicazioni')]")))
        page_details.execute_script("arguments[0].click();",click3)
        time.sleep(5)
    except:
        pass
    
    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > label.Attach_label'):
            data_text = single_record.text

        # Onsite Field -for key word "rettifica bando guue" in documents take notice type - "16"
        # Onsite Comment -ref url = "https://www.sanita.start.toscana.it/portalegare/index.php/bandi?getdettaglio=yes&bando=92874&tipobando=Bando&RicQ=YES&VisQ=SI&tipoDoc=BANDO_GARA_PORTALE&xslt=XSLT_BANDO_GARA_PORTALE&scadenzaBando=2024-01-22T18:00:00&jk="
            if data_text !='':
                attachments_data = attachments()
                external_url = single_record.get_attribute("onclick")
                attachments_data.external_url = external_url.split("open('")[1].split("');")[0].strip()

                try:
                    attachments_data.file_type = single_record.text.split(".")[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.file_name = single_record.text.split(attachments_data.file_type)[0].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments3: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        click1 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,"//*[contains(text(),'Tabella informativa di indicizzazione')]")))
        page_details.execute_script("arguments[0].click();",click1)
    except:
        pass
    
    try: 
        publish_date = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table_dpcm  td:nth-child(11)"))).get_attribute("outerHTML")
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        eligibility = page_details.find_element(By.CSS_SELECTOR, '#table_dpcm  td:nth-child(14)').get_attribute("outerHTML")
        notice_data.eligibility = eligibility.split(">")[1].split("<")[0].strip()
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass 
    # Onsite Field -for "Tabella informativa di indicizzazione / Indexing information table" use selector "#table_dpcm > table > tbody"  for "Chiarimenti / Clarifications" use selector  "#grigliaquesiti"
    # Onsite Comment - along with notice text (page detail) also take data from tender_html_element(main page) ---- //*[@id="table-lista-bandi"]/tbody/tr
    try:
        customer_details_data = customer_details()

        customer_details_data.org_name = org_name
    # Onsite Field -None         
    # Onsite Comment -	Indexing information table >>>>> Province Venue of Competition
        try:
            org_city = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table_dpcm"]/table/tbody/tr[3]/td[5]'))).get_attribute("outerHTML")
            customer_details_data.org_city = org_city.split(">")[1].split("<")[0].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -type_of_authority_code
    # Onsite Comment -	Indexing information table >>>>> Tipo di Amministrazione	
        try:
            type_of_authority_code = page_details.find_element(By.CSS_SELECTOR, '#table_dpcm  td:nth-child(4)').get_attribute("outerHTML")
            customer_details_data.type_of_authority_code = type_of_authority_code.split(">")[1].split("<")[0].strip()
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
    # Onsite Field -Incaricato
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -Indexing information table >>>> CPV code	
        cpv_code = page_details.find_element(By.CSS_SELECTOR, '#table_dpcm  td:nth-child(15)').get_attribute("outerHTML")
        cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = Doc_Download.page_details 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.sanita.start.toscana.it/portalegare/index.php/bandi?scaduti=no&tipobando="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="table-lista-bandi"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table-lista-bandi"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="table-lista-bandi"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
