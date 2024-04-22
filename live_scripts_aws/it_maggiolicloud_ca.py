from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_maggiolicloud_ca"
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
SCRIPT_NAME = "it_maggiolicloud_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'it_maggiolicloud_ca'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.currency = 'EUR'
    # Onsite Field -Titolo
    # Onsite Comment -None
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(2)').text.replace('Titolo :','')
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tipologia appalto
    # Onsite Comment -None
    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'form > div > div:nth-child(3)').text.replace('Tipologia appalto :','').strip()
        if "Servizi" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Service"
        elif "Lavori" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Works"
        elif "Forniture" in notice_data.contract_type_actual:
            notice_data.notice_contract_type ="Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.list-action > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,20)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    # Onsite Field -Data pubblicazione esito
    # Onsite Comment -None
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div > div:nth-child(5) > div:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    # Onsite Field -Riferimento procedura
    # Onsite Comment -None
    try:
        notice_data.notice_no = tender_html_element.text.split("CIG : ")[1].split("\n")[0].strip()
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//label[contains(text(),"Riferimento procedura : ")]/..').text.replace('Riferimento procedura :','').strip()
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    try:
        notice_data.related_tender_id = tender_html_element.text.split("Riferimento procedura :")[1].split("\n")[0].strip()
    except:
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ext-container > div > div > div > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Stazione appaltante
        # Onsite Comment -None
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//label[contains(text(),"Denominazione : ")]/..').text.replace('Denominazione :','')
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//label[contains(text(),"RUP : ")]/..').text.replace('RUP : ','').strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
# Onsite Field -click on lotti to get the data
# Onsite Comment -None
    try:
        Lotti_url = page_details.find_element(By.XPATH, '//a[contains(text(),"Lotti")]').get_attribute("href")
        fn.load_page(page_details1, Lotti_url, 80)
        time.sleep(2)
        logging.info(Lotti_url)
        time.sleep(2)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        
    try:
        lot_number = 1
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div .detail-section'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual 
            lot_details_data.contract_type = notice_data.notice_contract_type
            # Onsite Field -split from "Titolo" to "Tipologia appalto"
            # Onsite Comment -None
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR,'div:nth-child(2)').text.replace('Titolo :', '')
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
    
            try:
                lot_award_date = page_details1.find_element(By.XPATH, '//label[contains(text(),"Data aggiudicazione :")]/..').text
                lot_award_date = re.findall('\d+/\d+/\d{4}',lot_award_date)[0]
                lot_details_data.lot_award_date = datetime.strptime(lot_award_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in lot_award_date: {}".format(type(e).__name__))
                pass
        # Onsite Field -split from "Importo a base di gara" to "Stato"
        # Onsite Comment -None

            try:
                lot_netbudget = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3)').text
                lot_netbudget = lot_netbudget.split(':')[1].split('€')[0].replace('.', '').replace(',', '.')
                lot_details_data.lot_netbudget = float(lot_netbudget)
                lot_details_data.lot_netbudget_lc = lot_details_data.lot_netbudget
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass

        # Onsite Field -CIG
        # Onsite Comment -split from "Titolo" to "CIG"
            try:
                lot_actual = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2)').text
                if 'CIG:' in lot_actual:
                    cig_numbers = re.findall(r'CIG:\s*([A-Z0-9]+)', lot_actual)[0]
                    lot_details_data.lot_actual_number = cig_numbers
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            try:
                award_details_data = award_details()
                # Onsite Field -Ditta aggiudicataria
                # Onsite Comment -split data from "Ditta aggiudicataria " till  "Importo aggiudicazione "
                award_details_data.bidder_name = single_record.text.split('Ditta aggiudicataria : ')[1].split('\n')[0]
                # Onsite Field -Ditta aggiudicataria
                # Onsite Comment -split data from "Importo aggiudicazione"
                try:
                    netawardvaluelc = single_record.text.split("Importo aggiudicazione : ")[1].split('€')[0]
                    award_details_data.netawardvaluelc = float(netawardvaluelc.replace('.','').replace(',','.'))
                except:
                    pass
                # Onsite Field -Ditta aggiudicataria
                # Onsite Comment -split data from "Importo aggiudicazione"
                try:
                    award_details_data.netawardvalueeuro = award_details_data.netawardvaluelc
                except:
                    pass

                try:
                    award_date = page_details1.find_element(By.XPATH, '//label[contains(text(),"Data aggiudicazione :")]/..').text
                    award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                except:
                    pass
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            attachments_data.file_type = 'pdf'
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
        pass

# Onsite Field -Altri atti e documenti
# Onsite Comment -None

    try:
        documenti_url = page_details.find_element(By.XPATH, '//a[contains(text(),"Altri atti e documenti")]').get_attribute("href")
        fn.load_page(page_details2, documenti_url, 80)
    except:
        pass
    
    try:
        for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'a.bkg.pdf'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.text
            attachments_data.file_type = 'pdf'
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except:
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
    urls = ["https://appalti-villasofia-cervello.maggiolicloud.it/PortaleAppalti/it/ppgare_esiti_lista.wp;jsessionid=DD1A1BDE672576F71AEB086756093540.elda?_csrf=GCWK0XCFGSXEAECQ6M1JS4QHC9Z3OLUE"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div[position()>2 and position()<13]'))).text
                rows = WebDriverWait(page_main, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div[position()>2 and position()<13]')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div[position()>2 and position()<13]')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
                
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="pagination-navi"]/input[6]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ext-container"]/div/div/div/main/div/div[2]/form/div[position()>2 and position()<13]'),page_check))
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
