#NOTE- click on "RDO Aperte(0)" 

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
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_acquistinretepaopen_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_acquistinretepaopen_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'IT'
    
    # Onsite Field -N.GARA
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'regular-14 ng-binding').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -BANDO
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#page-complete  div > p > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -AREA MERCEOLOGICA
    # Onsite Comment -None

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.hidden-sm').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data e ora inizio presentazione offerte
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div:nth-child(3) > div > div > div > div > div.col-sm-10").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -SCADE IL
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.stato.nopadding.noBorderElenco.text-center.col-sm-1 > div").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),'Descrizione RdO:')]//following::p').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Descrizione
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),'Descrizione RdO:')]//following::p').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bandi/Categorie oggetto della RdO: ----------- split data from "Bandi/Categorie oggetto della RdO:" till "dash "-""
    # Onsite Comment -BENI- Supply, SERVIZI- Services 

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Bandi/Categorie ')]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Bandi/Categorie oggetto della RdO:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),'Bandi/Categorie ')]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#page-complete div > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-complete').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.col-xs-12.nopadding > div:nth-child(3) > div'):
            customer_details_data = customer_details()
        # Onsite Field -Ente committente:
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Ente committente:')]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.est_amount = tender_html_element.find_element(By.XPATH, 'div.col-md-1.ng-scope > div > div').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.grossbudgtlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-1.ng-scope > div > div').text
    except Exception as e:
        logging.info("Exception in grossbudgtlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=a361921199cb79dd"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#page-complete'):
            lot_details_data = lot_details()

        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, '#page-complete  div > p > a').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -CODICE CIG
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.borderME-left > div > div > div:nth-child(1) > div > div').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),'Bandi/Categorie ')]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
    # Onsite Field -Bandi/Categorie oggetto della RdO: ----------- split data from "Bandi/Categorie oggetto della RdO:" till "dash "-""
    # Onsite Comment -BENI- Supply, SERVIZI- Services 

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),'Bandi/Categorie ')]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass


        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.XPATH, '//*[contains(text(),'VALORE')]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),'VALORE')]//following::span[2]').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=446848221fc5f92d"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#page-complete'):
            lot_details_data = lot_details()

        
        # Onsite Field -CODICE CIG
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#sezione_lotti > div > div > div > div:nth-child(2) div > div').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.height80-sm.ng-scope.borderR-sm > div > div').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.CSS_SELECTOR, '#sezione_lotti > div div:nth-child(5) div > div').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, '#sezione_lotti > div div:nth-child(5) div > div').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    
# Onsite Field -NOTE ---FORMAT - 1
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#page-complete > div.ng-scope'):
            attachments_data = attachments()
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            try:
                attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.col-sm-5 > span').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.col-sm-5 > span').get_attribute('href')
            
        
        # Onsite Field -click on "RICHIESTE PARTECIPANTI"
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=4c2d107b87d84bc5"

            try:
                attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.col-sm-5 > span').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


# Onsite Field -NOTE ---FORMAT - 2
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#page-complete > div.ng-scope'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=446848221fc5f92d"

            try:
                attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.col-sm-11.borderR').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=446848221fc5f92d"

            attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.col-sm-11.borderR').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -ref url -"https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=446848221fc5f92d"

            try:
                attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.col-sm-11.borderR').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -use both the selector i.e. use selectors of format -1 and format -2 as this third format is a mixture of both format
# Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=bee3e98b3aa7c03d"

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#page-complete > div.ng-scope'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -ref url 

            try:
                attachments_data.file_name = tender_html_element.find_element(By.XPATH, '//*[@id="all-page"]/div[3]/div/div/div/div[7]/div[3]/div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -ref url -
            attachments_data.external_url = tender_html_element.find_element(By.XPATH, '//*[@id="all-page"]/div[3]/div/div/div/div[7]/div[3]/div').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -ref url -

            try:
                attachments_data.file_type = tender_html_element.find_element(By.XPATH, '//*[@id="all-page"]/div[3]/div/div/div/div[7]/div[3]/div').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=AB#!/%23post_call_position#post_call_position"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="page-complete"]/div/div[1]/div[6]/div[1]/div[3]/div'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
 