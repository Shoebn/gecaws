from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_aslnapoli1_ca"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_aslnapoli1_ca"
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
    notice_data.script_name = 'it_aslnapoli1_ca'
    
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
    notice_data.document_type_description = 'Contract Award'
    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data di pubblicazione
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -CIG
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Oggetto
    # Onsite Comment -None

    try:      
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.review36').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Procedura di scelta del contraente:
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procedura di scelta del contraente:")]').text.split(':')[1].split('-')[1].strip()
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_aslnapoli1_ca_procedure.CSV",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo dell'appalto:
    # Onsite Comment -None

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importi")]//following::div[1]').text.split(': € ')[1]
        notice_data.netbudgetlc = float(netbudgetlc.replace('.','').replace(',','.'))
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo dell'appalto:
    # Onsite Comment -None

    try:
        notice_data.netbudgeteuro = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgeteuro: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Importo dell'appalto:
    # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedura relativa:
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Procedure relative: ")]//following::a[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Ufficio:
        # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio:")]//following::a[1]').text

        # Onsite Field -RUP:
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"RUP:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Indirizzo:
        # Onsite Comment -click on 'Ufficio:' (div.campoOggetto114 > a) to get the data
        try:
            notice_url1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Ufficio:")]//following::a[1]').get_attribute('href')
            fn.load_page(page_details1,notice_url1)
        except:
            pass

        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::div[1]').text.split('Indirizzo: ')[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass


    # Onsite Field -Email certificate:
    # Onsite Comment -click on 'Ufficio:' (div.campoOggetto114 > a) to get the data

        try:
            customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email certificate:")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        customer_details_data = customer_details()
        customer_details_data.org_name=' ASL Naples 1 Centre'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)

    
# # Onsite Field -None
# # Onsite Comment -None

    try:       
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
#             Onsite Field -Oggetto
#             Onsite Comment -None
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
        
#         Onsite Field -None
#         Onsite Comment -None
        award_details_data = award_details()

        # Onsite Field -Aggiudicatari
        # Onsite Comment -None

        award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Aggiudicatari")]//following::ul[1]').text

        # Onsite Field -Importo di aggiudicazione:
        # Onsite Comment -None
        try:
            netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Importo di aggiudicazione:")]').text.split(': € ')[1].strip()
            award_details_data.netawardvaluelc = float(netawardvaluelc.replace('.','').replace(',','.'))
            award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
        except:
            pass

        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -Allegati
# # Onsite Comment -(ref url 'https://aslnapoli1centro.portaleamministrazionetrasparente.it/archivio11_bandi-gare-e-contratti_0_1084117_960_1.html')

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.campoOggetto48'):
            attachments_data = attachments()
        # Onsite Field -Allegato
        # Onsite Comment -split file_type from the given selector

        
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR, 'span').text
                if 'pdf' in file_type.lower():
                    attachments_data.file_type = 'pdf'
                elif 'zip' in file_type.lower():
                    attachments_data.file_type = 'zip'
                elif 'docx' in file_type.lower():
                    attachments_data.file_type = 'docx'
                elif 'xlsx' in file_type.lower():
                    attachments_data.file_type = 'xlsx'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass


            # Onsite Field -Allegato
            # Onsite Comment -split file_size from given selector

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'span').text.split('-')[-2].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            # Onsite Field -Allegato
            # Onsite Comment -take file_name in textform

            file_name = single_record.find_element(By.CSS_SELECTOR, 'div.campoOggetto48 > a').text
            attachments_data.file_name = file_name.replace(attachments_data.file_type,'')

            # Onsite Field -Allegato
            # Onsite Comment -None

            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

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
try:
    th = date.today() - timedelta(2)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://aslnapoli1centro.portaleamministrazionetrasparente.it/pagina960_affidamenti-diretti-di-lavori-servizi-e-forniture-di-somma-urgenza-e-di-protezione-civile.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[4]/div/main/div/div/div/div[2]/div/div/div[2]/div[2]/div/section/div[2]/table/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
