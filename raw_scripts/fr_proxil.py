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
SCRIPT_NAME = "fr_proxil"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_proxil'    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'   
    notice_data.notice_type = 4    
    notice_data.procurement_method = 2
    notice_data.notice_url = url
    
    # Onsite Field -Objet :
    # Onsite Comment -take only "objet"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.post-block > table > tbody > tr > td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet :
    # Onsite Comment -take only "objet"
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split notice_no  from this path

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.post-title > table > tbody > tr > td').text.split(' - ')[1].split('(')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    # Onsite Field -None
    # Onsite Comment -take only publish date from this path

    try:                                                                
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div > div:nth-child(2) > div > div.post-block > table > tbody > tr:nth-child(1) > td").text
        publish_date = GoogleTranslator(source='fr', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div:nth-child(4) > table > tbody").text
            publish_date = GoogleTranslator(source='fr', target='en').translate(publish_date)
            publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -take only notice deadliine from this path

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.post-block > table > tbody > tr:nth-child(3)").text
        notice_deadline = GoogleTranslator(source='fr', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take only  type_of_procedure_actual from this path

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.post-block > table > tbody > tr:nth-child(2) > td').text.split('Type de procédure :')[1]
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = 'ANNONCES'
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -None
    # Onsite Comment -split org_name from this path

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.post-title > table > tbody > tr > td').text.split(' - ')[0]
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
     
# Onsite Field -None
# Onsite Comment -None
    try:
        url1='https://www.proxilegales.fr'
        res = tender_html_element.find_element(By.CSS_SELECTOR, 'div.post-button').get_attribute('onclick')
        res=res.split('("')[1].split('",')[0]
        notice_data.notice_url=url1+res
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.XPATH, '/html/body/div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    

    try:
        notice_type = page_details.find_element(By.CSS_SELECTOR, 'body > div > table.content > tbody > tr:nth-child(9) > td').text
        if "AVIS D'ATTRIBUTION" in notice_type:
            notice_data.notice_type = 7
    except:
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH,"//*[contains(text(),'Type de marché :')]//following::td[1]").text
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif 'Fournitures - Achat' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Travaux - Exécution' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        else:
            notice_data.notice_contract_type = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:              
        lot_number = 1
        lot_title = page_details.find_element(By.CSS_SELECTOR, 'body > div > table.content > tbody > tr:nth-child(9) > td').text.split('\n')
        lot_details_data = lot_details()     
        try:
            for lots in lot_title:
                if 'Lot 0' in lots:    
                    lot_details_data.lot_title = lots.split('-')[1].strip()
                elif 'Lot n°0' in lots:
                    lot_details_data.lot_title = lots.split(':')[1].strip()
                elif 'Lot ' in lots:
                    lot_details_data.lot_title = lots.split(',')[1].strip()
                else:
                    lot_details_data.lot_title = notice_data.notice_title
        except:
            lot_details_data.lot_title = notice_data.notice_title
        try:
            data = page_details.find_element(By.CSS_SELECTOR, 'body > div > table.content > tbody > tr:nth-child(9) > td').text.split('\n')
            for bidder_name in data:
                if 'Nom du titulaire :' in bidder_name:
                    award_details_data = award_details()
                    award_details_data.bidder_name = bidder_name.split(':')[1].strip()
                    if 'Montant du marché :' in bidder_name:
                        award_details_data.final_estimated_value = float(bidder_name.split(':')[1].strip())
                    if "Date d'attribution :" in bidder_name:
                        award_date = re.findall('\d+/\d+/\d{2}',bidder_name)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%y').strftime('%Y/%m/%d')
                    elif "Date d'attribution :" in bidder_name:
                        award_date = re.findall('\d+/\d+/\d{4}',bidder_name)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_number = lot_number
        lot_details_data.contract_type = notice_data.notice_contract_type
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
        lot_number += 1

    except Exception as e:
        logging.info("Exception in lot_details: ", str(type(e))) 
        pass

    try:
        cpvs = page_details.find_element(By.CSS_SELECTOR,'body > div > table.content > tbody > tr:nth-child(9) > td').text
        if 'Code CPV :' in cpvs:
            cpvs_data = cpvs()
            cpvs_data.cpvs = cpvs.split('Code CPV :')[1].split('\n')[0].strip()  
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
              
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    fromth = th.strftime("%d/%m/%Y")
    toth = date.today().strftime("%d/%m/%Y") 
    urls = ['https://www.proxilegales.fr/publisher_portail/public/annonce/afficherAnnonces.jsp;jsessionid=4B78CDCFD3FFACD500DD95BB19C74C60;jsessionid=473B0862937B82073652819A473E8635;jsessionid=C1D8241F1FF6E7DDAC7A94F3784361F5?filtreType=&loadCriteria=true&type_avis=tout&tri=marche.date_dern_modif%20desc&iIdDepartement=&type_annonce=&iIdMarcheType=&bDisplaySearchEngine=false&bLaunchSearch=true&sIsAnnonceDemat=&sIsAnnonceDce=&sIsOnlyUnreadedAnnonceChecked=&iIdGroupCompetence=&se_tsStartDate='+str(fromth)+'&se_tsEndDate='+str(toth)+'&se_iMaxElementPerPage=5&se_bDisplayMapAnnounce=false&numPage=0#ancreHP'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="page-modula"]/div[4]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-modula"]/div[4]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-modula"]/div[4]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="page-modula"]/div[4]'),page_check))
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
