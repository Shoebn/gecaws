from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_klekoon"
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
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_klekoon"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
      
    notice_data.script_name = 'fr_klekoon'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.row.bg-light-grey.no-gutters.p-2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.bg-light-grey > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
        
    try:
        close_window_msg = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="form_demande"]/div/div[1]/div[3]/button/span/i')))
        page_details.execute_script("arguments[0].click();",close_window_msg)
        time.sleep(3)
    except:
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
     
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, " div.col-md-2.kle-border-right.kle-border-bottom.bg-light-grey > div.row.no-gutters.align-items-center.h-50.kle-border-bottom > div > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Clôture :
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "div.col-md-2.kle-border-right.kle-border-bottom.bg-light-grey > div:nth-child(2) > div > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').text
        dispatch_date = dispatch_date.split('Date d’envoi du présent avis à la consultation : ')[1]
        dispatch_date = dispatch_date.split('\n')[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Catégorie de marché :
    # Onsite Comment -1. split notice_contract_type after this keyword "Catégorie de marché :".    2.Replace follwing keywords with given respective kywords ('Services =Service','Travaux = Works ',' Fournitures = Supply')

    try:
        notice_contract_type = page_details.find_element(By.CSS_SELECTOR, 'td > div.row.mt-4 > div.col > div:nth-child(2) > div').text
        notice_contract_type = notice_contract_type.split('Catégorie de marché :')[1]
        notice_contract_type = notice_contract_type.split('\n')[0]
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Travaux' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Fournitures' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration =  page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').text.split('Durée en mois :')[1].split("\n")[0]
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    # Onsite Field -Description succincte du marché :
    # Onsite Comment -1.split notice_summary_english after "Description succincte du marché :"this keyword.   2.if not availabel then take local_title as notice_english_summary.

    # take "T.NOTICE_SUMMARY_ENGLISH" in english language 
    # T.NOTICE_SUMMARY_ENGLISH	  = take data fron "1.2) Description du marché :" 
 
    try:
        notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').text
        notice_summary_english = notice_summary_english.split("Description du marché :\n")[1]
        notice_data.local_description = notice_summary_english.split('\n')[0]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
   
    try:
        notice_no = page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').text.split('Référence de la consultation :')[1]
        notice_data.notice_no = notice_no.split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Source :
    # Onsite Comment -1.here "Klekoon - Adapted procedure" don't grab 'Klekoon'.
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "/html/body/section/div/div[2]/div/div/div/div[2]/div[1]/div[2]/div/span").text.split('-')[1].strip()
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_klekoon_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data = customer_details()
# Onsite Field -None
# Onsite Comment -split org_name after "Acheteur public"

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.row.no-gutters.align-items-center.h-50.kle-border-bottom:nth-child(1) div.col.pl-3.pt-2.pb-2 > span.text-black').text.split("Emetteur :")[1].strip()
    # Onsite Field -None
    # Onsite Comment -for org_address 		eg.,public buyer 		    SAINT AVOLD TOWN HALL 		    36 Boulevard de Lorraine 		    57500 SAINT AVOLD FR 		    Telephone: 0387911007; Fax: 0387913647 			here take only 	36 Boulevard de Lorraine 		    			57500 SAINT AVOLD FR		in org_address

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div.col-8.col-lg-10 > p').text.split("\n")[1:-1]
            org_address=",".join(org_address)
            customer_details_data.org_address =org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
    # Onsite Field -Téléphone :
    # Onsite Comment -split org_phone after "Téléphone : "

        try:
            org_phone = page_details.find_element(By.CSS_SELECTOR, 'div.col-8.col-lg-10').text.split('Téléphone : ')[1]
            customer_details_data.org_phone = org_phone.split(' ')[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').text.split('Code NUTS :')[1]
            customer_details_data.customer_nuts = customer_nuts.split('\n')[1]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
    # Onsite Field -Fax :
    # Onsite Comment -split org_fax after "Fax  "

        try:
            customer_details_data.org_fax = page_details.find_element(By.CSS_SELECTOR, 'div.col-8.col-lg-10').text.split(' Fax : ')[1].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__)) 
        pass
  
    try:   
        tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.blok.detail-consultation > div:nth-child(1) > div').text.split("Critères d'attribution")[1]
        tender_criteria_title = tender_criteria_title.split('\n\n\n')[0]           
        for criteria_title in tender_criteria_title.split('\n'):
            # Onsite Field -Critères d’attribution :
            # Onsite Comment -split tender_criteria_title after "Critères d’attribution :"
            if 'Pondération' in criteria_title:
                tender_criteria_data = tender_criteria()
                tender_criteria_title = str(criteria_title)
                tender_criteria_data.tender_criteria_title = GoogleTranslator(source='auto', target='en').translate(tender_criteria_title)
                tender_criteria_data.tender_criteria_weight = criteria_title.split(':')[1]    
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__)) 
        pass
    
    try:
        lots = page_details.find_element(By.XPATH,"//*[contains(text(), 'Liste des lots')]//following::table[1]").text
        if 'Lot' in lots:
            lot_number = 1
            for lot in lots.split('Lot')[1:]:
                if lot != '':
                    lot_details_data = lot_details()
                    lot_details_data.contract_type=notice_data.notice_contract_type
                    lot_details_data.lot_number = lot_number
                    
                    lot_details_data.lot_title = lot.split(':')[1].strip()
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                    try:
                        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.row.mt-4 > div > div:nth-child(4) > div > table > tbody > tr '):
                            lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, ' td > div:nth-child(2)').text.split("Critère de sélection des offres")['\n']
                            for criteria_title in lot_criteria_title:
                                lot_criteria_data = lot_criteria()
                                lot_criteria_title = criteria_title.split("(")[0]
                                lot_criteria_data.lot_criteria_title = GoogleTranslator(source='auto', target='en').translate(lot_criteria_title)
                                lot_criteria_weight = criteria_title.split('(')[1].split("points")[0]
                                lot_criteria_data.lot_criteria_weight =int(lot_criteria_weight)
                                lot_criteria_data.lot_criteria_cleanup()
                                lot_details_data.lot_criteria.append(lot_criteria_data)
                    except Exception as e:
                        logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                        pass
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number+=1
    except:
        pass     
    # Onsite Field -None
    # Onsite Comment -take attachment_details after clicking on "div.row.no-gutters.bg-light-grey > div:nth-child(4) > div > a" in tender_html_element

    try:      
        attachments_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.icone-piece.position-relative.text-black.pointer > p:nth-child(3)')))
        page_details.execute_script("arguments[0].click();",attachments_click)
        time.sleep(3)
    except:
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > section > div > div.blok.dce-marche > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        file_name = page_details.find_element(By.CSS_SELECTOR, 'td.pl-3.py-3 > div > span').text.split(".")[0]
        if file_name != "":
            attachments_data = attachments()
            attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'td.pl-3.py-3 > div > span').text.split(".")[0]
            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'td.pl-3.py-3 > div > span').text.split('.')[1]
                file_size = page_details.find_element(By.CSS_SELECTOR, 'tbody:nth-child(2) > tr:nth-child(1) > td.text-center').text
                file_size = GoogleTranslator(source='fr', target='en').translate(file_size)
                attachments_data.file_size = fn.bytes_converter(file_size)
            except:
                pass
            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(2) > td > a').get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in file_name: {}".format(type(e).__name__))
        pass
   
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
chrome_options = Options()
for argument in arguments:
    chrome_options.add_argument(argument)
page_main = webdriver.Chrome(chrome_options=chrome_options)
page_details = webdriver.Chrome(chrome_options=chrome_options) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.klekoon.com/rechercher-une-annonce-ou-un-dce-dematerialise-sur-klekoon"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,15):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.col.kle-border'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.col.kle-border')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.col.kle-border')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
                try:
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'div.col.kle-border'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
