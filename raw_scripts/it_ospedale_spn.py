
#NOTE ---Use VPN for the URL

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
SCRIPT_NAME = "it_ospedale_spn"
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
    notice_data.script_name = 'it_ospedale_spn'
    
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
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -if the title start with "AVVISO ESPLORATIVO di MANIFESTAZIONE DI INTERESSE" notice type will be = 5 --- ref url "https://www.ospedale.perugia.it/bandi/avviso-esplorativo-di-manifestazione-di-interesse-procedura-negoziata-senza-bando-in-modalita-telematica-finalizzata-alla-fornitura-in-service-di-un-frazionatore-iniettore-automatico-per-radiofarmaci-occorrente-alla-s-c-medicina-nucleare-della-aziend"
                #     if the attachment having keyword "Errata Corrige.pdf" than it is Notice type = 16 --- ref url "https://www.ospedale.perugia.it/bandi/avviso-di-consultazione-preliminare-di-mercato-per-la-fornitura-di-broncoscopi-monouso"
                #     if you get following keywords in notice text "AGGIUDICATARIO" and "IMPORTO AGGIUDICAZIONE" take notice type "7" --- ref url "https://www.ospedale.perugia.it/bandi/lavori-di-adeguamento-delle-strutture-ed-impianti-esistenti-in-funzione-della-installazione-di-una-pettac-per-il-reparto-di-medicina-nucleare-al-piano-1-del-blocco-p"
    
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot   p:nth-child(1) > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-sx.col-xs-12.col-md-7 > div > h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DATA PUBBLICAZIONE
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > p:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -SCADENZA
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot  div >  p:nth-child(3) > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Leggi tutto
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'p:nth-child(4) >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-sx.col-xs-12.col-md-7').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sx.col-xs-12.col-md-7'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'L’Azienda Ospedaliera di Perugia'
            customer_details_data.org_parent_id = '1322722'
            customer_details_data.org_phone = '075 5781'
            customer_details_data.org_email = 'acquistiappalti.aosp.perugia@postacert.umbria.it'
            customer_details_data.org_address = 'sant andrea delle frattle - 06129 PERUGIA'
            customer_details_data.org_language = 'IT'
            customer_details_data.org_country = 'IT'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass



# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sx.col-xs-12.col-md-7'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot p:nth-child(1) > span').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sx.col-xs-12.col-md-7'):
                    award_details_data = award_details()
		
                    # Onsite Field -Aggiudicatario
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Aggiudicatario')]').text
			
                    # Onsite Field -Importo aggiudicazione
                    # Onsite Comment -None

                    award_details_data.netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),' Importo aggiudicazione')]').text
			
                    # Onsite Field -Importo aggiudicazione
                    # Onsite Comment -None

                    award_details_data.netawardvalueeuro = page_details.find_element(By.XPATH, '//*[contains(text(),' Importo aggiudicazione')]').text
			
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
    
# Onsite Field -ALLEGATI
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#ctl00_cphBody_pnlPagina article:nth-child(2) > div:nth-child(2)'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'article:nth-child(2) > div:nth-child(2) > div').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -just take title dont take extensions ---- eg"pdf"

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'article:nth-child(2) > div:nth-child(2) > div').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'article:nth-child(2) > div:nth-child(2) > div').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass




    #NOTE - from the following link  "https://www.ospedale.perugia.it/pagine/bandi-di-gara-e-contratti" >>>>> use "p:nth-child(4) >a" for page detail >>>  click on "lINK GARA" use selector " p:nth-child(2) > span > a" for page detail1  >>>> add details from page_detail and page_detail1 - following is the code UPDATE it in the script

    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(2) > span > a').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass


    # Onsite Field -Categorie
    # Onsite Comment -None

    try:
        notice_data.category = page_details1.find_element(By.CSS_SELECTOR, 'div.A65JXVB-jb-l').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'body > div.A65JXVB-N-a > div > div.A65JXVB-eb-a.A65JXVB-h-n.A65JXVB-n-a > div.A65JXVB-eb-d.A65JXVB-eb-g > div > div:nth-child(3) > div:nth-child(2) > div > div > div:nth-child(4) > div > div.A65JXVB-A-b > div.A65JXVB-A-a > div > div > div'):
            attachments_data = attachments()
        # Onsite Field -Descrição
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details1.find_element(By.CSS_SELECTOR, 'td.A65JXVB-v-b.A65JXVB-w-a.null.x-grid-item-focused').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, 'td.A65JXVB-v-b.A65JXVB-w-a.x-grid-cell-first.null.x-grid-item-focused').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details1.find_element(By.CSS_SELECTOR, 'td.A65JXVB-v-b.A65JXVB-w-a.x-grid-cell-first.null.x-grid-item-focused').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ospedale.perugia.it/pagine/bandi-di-gara-e-contratti"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,20):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div'),page_check))
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
    