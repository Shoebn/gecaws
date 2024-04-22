from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_stella_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
import os
import csv
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.support.ui import Select
import gec_common.web_application_properties as application_properties
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_stella_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_stella_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'
    notice_data.additional_source_name = 'Servizio Contratti Pubblic'
    
    try:
        published_date = tender_html_element['pubDate']
        published_date = re.findall('\d+/\d+/\d{4}',published_date)[0]
        notice_data.publish_date= datetime.strptime(published_date,'%d/%m/%Y').strftime("%Y/%m/%d")
        logging.info(notice_data.publish_date)
    except:
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.document_type_description = tender_html_element['TipoDoc']
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.notice_no = tender_html_element['CIG']
        if notice_data.notice_no == '' or notice_data.notice_no == None:
            notice_data.notice_no = tender_html_element['RegistroSistema']
        notice_data.tender_id = notice_data.notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass



    try:
        notice_deadline = tender_html_element['DtScadenzaBandoTecnical']
        date_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        time_deadline = re.findall('\d+:\d+:\d+',notice_deadline)[0]
        notice_deadline = date_deadline +" "+ time_deadline
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element['TitoloDocumento']
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_contract_type = tender_html_element['Contratto']
        notice_data.contract_type_actual = tender_html_element['Contratto']
        if 'Forniture' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Servizi' in notice_contract_type or 'Lavori' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        t_id = tender_html_element['IdMsg']
    except Exception as e:
        logging.info("Exception in t_id: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_url = 'https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc='+str(t_id)+'&tipo_doc=BANDO_GARA_PORTALE'
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url


    try:
        notice_data.notice_text += WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#collapse1 > div'))).get_attribute("outerHTML")
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try: 
        notice_data.local_description = tender_html_element['Oggetto']
        notice_data.notice_summary_english=GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo Appalto:")]//following::div[1]').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        notice_data.netbudgetlc =float(netbudgetlc.replace('.','').replace(',','.').strip())
        notice_data.netbudgeteuro = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass

    try:              
        tender_criteria_data = tender_criteria()
    # Onsite Field -Criterio Aggiudicazione:
    # Onsite Comment -None

        tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Criterio Aggiudicazione:")]//following::div').text
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:               
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#collapse1n > div > div > div'):
            attachments_data = attachments()
        # Onsite Field -Documentazione
        # Onsite Comment -split the file type , for ex . " DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx" here split only "docx", ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

            try:
                file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('.')[-1].strip()
                if 'pdf' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'zip' in file_type:
                    attachments_data.file_type = 'zip'
                elif 'docx' in file_type:
                    attachments_data.file_type = 'docx'
                elif 'xls' in file_type:
                    attachments_data.file_type = 'xls'
                elif 'xlsx' in file_type or 'XLSX' in file_type:
                    attachments_data.file_type = 'xlsx'
                elif 'doc' in file_type:
                    attachments_data.file_type = 'doc'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -Documentazione
        # Onsite Comment -split only file_name for ex."Disciplinare di gara:  DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx", here split only "Disciplinare di gara",     split the data before " :(colon) "    url ref : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'span').text.split(':')[0].strip()

        # Onsite Field -Documentazione
        # Onsite Comment -split the file description , for ex."DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO.docx" here split only "DISCIPLINARE (Ripristinato automaticamente) PREZZO PIù BASSO", ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1595414&tipo_doc=BANDO_GARA_PORTALE"
            try:
                file_description = single_record.find_element(By.CSS_SELECTOR, 'a').text
                if ':' in file_description and '.pdf' in file_description:
                    attachments_data.file_description = file_description.split(':')[1].split('.pdf')[0].strip()
                elif '.pdf' in file_description:
                    attachments_data.file_description = file_description.split('.pdf')[0].strip()
                elif ':' in file_description and '.docx' in file_description:
                    attachments_data.file_description = file_description.split(':')[1].split('.docx')[0].strip()
                elif '.docx' in file_description:
                    attachments_data.file_description = file_description.split('.docx')[0].strip()
                elif ':' in file_description and '.doc' in file_description:
                    attachments_data.file_description = file_description.split(':')[1].split('.doc')[0].strip()
                elif '.doc' in file_description:
                    attachments_data.file_description = file_description.split('.doc')[0].strip()
                else:
                    attachments_data.file_description = file_description
            except Exception as e:
                logging.info("Exception in file_description: {}".format(type(e).__name__))
                pass

        # Onsite Field -Documentazione
        # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:               
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Avvisi di Rettifica")]//following::div/div/div/a'):

            file_name = single_record.get_attribute('innerHTML')

            if len(file_name) > 0:

                attachments_data = attachments()

                attachments_data.file_name = single_record.get_attribute('innerHTML')

                attachments_data.external_url = single_record.get_attribute('href')

                try:
                    if 'pdf' in  attachments_data.external_url:
                        attachments_data.file_type = 'pdf'
                    elif 'zip' in  attachments_data.external_url:
                        attachments_data.file_type = 'zip'
                    elif 'docx' in  attachments_data.external_url:
                        attachments_data.file_type = 'docx'
                    elif 'xls' in  attachments_data.external_urle:
                        attachments_data.file_type = 'xls'
                    elif 'xlsx' in  attachments_data.external_url or 'XLSX' in  attachments_data.external_url:
                        attachments_data.file_type = 'xlsx'
                    elif 'doc' in file_type:
                        attachments_data.file_type = 'doc'
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass



                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
            else:
                pass
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Ente Appaltante:
    # Onsite Comment -split the data from  "DETTAGLIO" this section,

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ente Appaltante:")]//following::div').text

        if customer_details_data.org_name == '':
            customer_details_data.org_name = 'Centrale acquisti'

    # Onsite Field -Incaricato:
    # Onsite Comment -split the data from "DETTAGLIO " this section

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Incaricato")]//following::div').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            TABELLA_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="heading3"]/button')))
            page_details.execute_script("arguments[0].click();",TABELLA_clk)
        except:
            pass
        time.sleep(5)
    # Onsite Field -Comune Sede di Gara:
    # Onsite Comment -click on "TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the details > selector = "#heading3 > button",

        try:
            customer_details_data.org_city = WebDriverWait(page_details, 30).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Comune Sede di Gara:")]//following::div'))).text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Indirizzo Sede di Gara:
    # Onsite Comment -click on "TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the details > selector = "#heading3 > button",           ref url : "https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza/dettaglio-bando?id_doc=1655057&tipo_doc=BANDO_GARA_PORTALE"

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Indirizzo Sede di Gara:")]//following::div').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Tipo di Amministrazione:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -TABELLA INFORMATIVA DI INDICIZZAZIONE
# Onsite Comment -click on " TABELLA INFORMATIVA DI INDICIZZAZIONE" this drop down for split the cpv code
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"URL di pubblicazione su")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
     
    try:
        cpvs_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV:")]').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass

    try:
        class_codes_at_source = ''
        class_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Codice CPV:")]').text
        cpv_regex = re.compile(r'\d{8}')
        class_codes_at_source_data = cpv_regex.findall(class_code)
        for class_codes_at_source1 in class_codes_at_source_data:
            class_codes_at_source += class_codes_at_source1
            class_codes_at_source += ','
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
        notice_data.cpv_at_source = notice_data.class_codes_at_source
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="portlet_it_lazio_centraleacquisti_bandogaradettaglio_BandoGaraDettaglioPortlet_INSTANCE_yN0S0eNTtnct"]/div/div[2]/div/app-root/div/app-dettaglio-bando/div/div'))).get_attribute("outerHTML")
        notice_data.notice_text = re.sub('<svg.*?>|</svg>', '', notice_data.notice_text)
    except:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost'] 
page_details = fn.init_chrome_driver(arguments) 
tmp_dwn_dir = application_properties.TMP_DIR#.replace('/',"\\")  #for linux remove --> .replace('/',"\\")
experimental_options = {"prefs": {"download.default_directory": tmp_dwn_dir}}
page_main = fn.init_chrome_driver(arguments=[], experimental_options = experimental_options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)

    url = 'https://centraleacquisti.regione.lazio.it/bandi-e-strumenti-di-acquisto/bandi-di-gara-in-scadenza?t=Bandi&ente=regione'
    logging.info(url)
    logging.info('----------------------------------')
    fn.load_page(page_main, url,80)

    clk = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//button[@class="btn btn-primary"]')))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(5)
    pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#listSearch1'))
    pp_btn.select_by_index(2)
    time.sleep(10)

    clk = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pills-tab > li:nth-child(3) > app-pulsante > button > span' )))
    page_main.execute_script("arguments[0].click();",clk)
    time.sleep(10)
    with open(application_properties.TMP_DIR+"/exportBandiGaraCSV.csv", 'r', encoding="utf8") as f:
        lines = f.readlines()[2:]  # Skip the first two rows
        dict_reader = csv.DictReader(lines)
        BandiGaraCSV = list(dict_reader)
      
    for tender_html_element in BandiGaraCSV:
        extract_and_save_notice(tender_html_element)
        if notice_count >= MAX_NOTICES:
            break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
    os.remove(application_properties.TMP_DIR+"/exportBandiGaraCSV.csv")
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()  
    output_json_file.copyFinalJSONToServer(output_json_folder)
