from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_rimini_ca"
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
SCRIPT_NAME = "it_rimini_ca"
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
    notice_data.script_name = 'it_rimini_ca'
    
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
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.document_type_description = 'Avvisi di aggiudicazione, esiti e affidamenti'
    
    # Onsite Field -Titolo :
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-item> div:nth-child(2)').text.split("Titolo :")[1]
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -Replace following keywords with given respective keywords ('Lavori = service' , 'Forniture = supply' , 'Servizi   = service')
    
    # Onsite Field -Tipologia appalto :
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-item> div:nth-child(3)').text.split("Tipologia appalto :")[1].strip()
        if 'Lavori' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Forniture' in notice_data.contract_type_actual: 
            notice_data.notice_contract_type = 'Supply'  
        elif 'Servizi' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service' 
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Data pubblicazione esito :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "form > div div:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Procedure reference:
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div div:nth-child(6)').text.split("Riferimento procedura : ")[1]
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
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
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.column.content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
     # Onsite Field -CIG :
    # Onsite Comment -None
     # Onsite Field -Visualizza scheda
    # Onsite Comment -if notice_no is not available in "CIG :" field then pass notice_no from notice_url

    
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div div:nth-child(4').text.split("CIG :")[1]
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = re.findall('\w+\d{5}',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Stazione appaltante
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(1)').text.split("Stazione appaltante :")[1]

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
    # Onsite Field -RUP
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.detail-section.first-detail-section > div:nth-child(3)').text.split("RUP :")[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Documentazione esito di gara
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > ul > li form'):
            doc_url = single_record.get_attribute('action')
            fn.load_page(page_details3,doc_url,100)
            
            for single_record in page_details3.find_elements(By.CSS_SELECTOR, 'a.bkg'):
                attachments_data = attachments()
    
                try:
                    attachments_data.file_name = single_record.text
                except Exception as e:
                    logging.info("Exception in file_name: {}".format(type(e).__name__))
                    pass            

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div:nth-child(7) > ul > li > a"))).get_attribute("href")                     
        logging.info(lot_url)
        fn.load_page(page_details1,lot_url,100)
        time.sleep(3)
    except:
        pass
    
# Onsite Field -None
# Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for lot_details

    try:              
#         for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.container div > div.column.content > div'):
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Titolo :
        # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for lot_details and grab the data from "Titolo :" field

        lot_details_data.lot_title = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section div:nth-child(2)').text.split("Titolo :")[1]
        
        try:
            lot_details_data.lot_actual_number = lot_details_data.lot_title.split("CIG:")[1]
        except:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Importo a base di gara :
        # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for lot_details and grab the data from "Importo a base di gara :" field

        try:
            lot_grossbudget = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section div:nth-child(3)').text.split("Importo a base di gara :")[1]
            lot_grossbudget = re.sub("[^\d\.\,]","",lot_grossbudget)
            lot_details_data.lot_grossbudget =float(lot_grossbudget.replace(',','.').replace('.','').strip())
            lot_details_data.lot_grossbudget = lot_details_data.lot_grossbudget
            lot_details_data.lot_grossbudget_lc = lot_details_data.lot_grossbudget
        except Exception as e:
            logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
            pass

        # Onsite Field -Importo a base di gara :
        # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for lot_details and grab the data from "Importo a base di gara :" field

        # Onsite Field -None
        # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for award_details

        try:
            award_details_data = award_details()

            # Onsite Field -Ditta aggiudicataria :
            # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for award_details

            award_details_data.bidder_name = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section div:nth-child(4)').text.split("Ditta aggiudicataria :")[1]

            # Onsite Field -Importo aggiudicazione :
            # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for award_details,  ref_url of detail_page 1 : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G07215&ext=&_csrf=5NOGW3VVOMBBJ2DG9J9FGJJR5SYEEYZ5"

            grossawardvaluelc = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section div:nth-child(5)').text.split("Importo aggiudicazione :")[1]
            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
            award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','.').replace('.','').strip())
            award_details_data.grossawardvalueeuro = award_details_data.grossawardvaluelc

            # Onsite Field -Importo aggiudicazione :
            # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for award_details,  ref_url of detail_page 1 : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G07215&ext=&_csrf=5NOGW3VVOMBBJ2DG9J9FGJJR5SYEEYZ5"


            # Onsite Field -Data aggiudicazione :
            # Onsite Comment -in detail_page click on "Lotti" ( selector: "div:nth-child(7) > ul > li > a" ) for award_details,  ref_url of detail_page 1 : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewLotti.action&currentFrame=7&codice=G07215&ext=&_csrf=5NOGW3VVOMBBJ2DG9J9FGJJR5SYEEYZ5"

            award_date = page_details1.find_element(By.CSS_SELECTOR, 'div.detail-section div:nth-child(6)').text.split("Data aggiudicazione : ")[1]
            award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')

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
    
    try:
        attach_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div:nth-child(8) > ul > li > a"))).get_attribute("href")                     
        logging.info(attach_url)
        fn.load_page(page_details2,attach_url,100)
        time.sleep(3)
    except:
        pass
    
# Onsite Field -Altri atti e documenti >> Documenti
# Onsite Comment -in detail_page click on  "Altri atti e documenti" ( selector : div:nth-child(8) > ul > li > a  ) for documents ,   ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewAttiDocumenti.action&currentFrame=7&codice=G08282&ext=&_csrf=9HHZQKRHR2DUSAOPHTNM6LMSD1CRJ7D8"

    try:              
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'div.detail-section > div > ul > li > a'):
            attachments_data = attachments()
        # Onsite Field -Altri atti e documenti >> Documenti
        # Onsite Comment -take only as a text format .  ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewAttiDocumenti.action&currentFrame=7&codice=G08282&ext=&_csrf=9HHZQKRHR2DUSAOPHTNM6LMSD1CRJ7D8"

            try:
                attachments_data.file_name = single_record.text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Altri atti e documenti >> Documenti
        # Onsite Comment -ref_url : "https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?actionPath=/ExtStr2/do/FrontEnd/Esiti/viewAttiDocumenti.action&currentFrame=7&codice=G08282&ext=&_csrf=9HHZQKRHR2DUSAOPHTNM6LMSD1CRJ7D8"

            attachments_data.external_url = single_record.get_attribute('href')
        
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
page_details3 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://appaltiecontratti.comune.rimini.it/PortaleAppalti/it/ppgare_esiti_lista.wp?_csrf=AQ9AOEPPPRV97KYWS97XM6K5SLHXS9EM"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.list-item'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.list-item')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#pagination-navi > input.nav-button.nav-button-right")))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
