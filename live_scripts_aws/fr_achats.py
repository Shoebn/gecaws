from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_achats"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fr_achats"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_achats'

    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    dropdown_clk = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.col-3.d-none.d-lg-block > a')))
    page_main.execute_script("arguments[0].click();",dropdown_clk)
    time.sleep(7)
    
    try:
        notice_data.document_type_description = WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.col-lg-9.col-12.text-dark > span'))).text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(2)   div.col-lg-9.col-12.text-dark').text
        if 'Fournitures' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "li:nth-child(4)  div.col-lg-9.col-12.text-dark").text  
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline  = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-7 > span").text  
        notice_deadline  = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline  = datetime.strptime(notice_deadline ,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline : {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-lg-8.col-10 > h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(1)  div.col-lg-11.col-10 > span').text  
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:              
        cpvs_data = cpvs()
        cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'li:nth-child(3) > div > div.col-lg-9.col-12.text-dark').text 
        cpvs_data.cpv_code  = cpv_code.split('(')[1].split(')')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass    

    dropdown_clkk = tender_html_element.find_element(By.CSS_SELECTOR,"div.col-3.d-none.d-lg-block > a")
    page_main.execute_script("arguments[0].click();",dropdown_clkk)
    time.sleep(4)

    notice_data.notice_url = 'https://www.achats.defense.gouv.fr/marches-publics/appels-d-offres?type-search=region&type-cloture=none&date-debut=&date-fin=&q=&page=&sort=&segment=&currenttab=appel-offres&type-marches%5B%5D=appel-offres&type-marches%5B%5D=rfi&type-marches%5B%5D=programmation'

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Ministère des Armées'
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.org_parent_id = '7349822'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
                
    try:
        lot_clck = tender_html_element.find_element(By.CSS_SELECTOR,'div.card-body.p-0 > ul > li.list-group-item.container.border-0.p-2.pl-3 > div > div.col-lg-5.col-12 > a')
        page_main.execute_script("arguments[0].click();",lot_clck)
        time.sleep(5)
        lot_number = 1
        for l in page_main.find_elements(By.CSS_SELECTOR,'#accordionLots > div'):
            lot_details_data = lot_details()
            l.find_element(By.CSS_SELECTOR,'#accordionLots > div:nth-child(n) > div.card-header.bg-white > div > div.col-2 > a > i').click()
            time.sleep(5)
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = l.find_element(By.CSS_SELECTOR,'div.card-header.bg-white > div > div.col-10 > p > span.text-secondary').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            lot_description = l.find_element(By.CSS_SELECTOR,'div.collapse > div > ul').text
            lot_details_data.lot_description = lot_description.split('Description :')[1].split('Domaine')[0].strip()
            lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            
            try:
                cpv = lot_description.split('Domaine :')[1].strip()
                cpv_regex = re.compile(r'\d{8}')
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = cpv_regex.findall(cpv)[0]
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__)) 
                pass
            
            lot_details_data.contract_type = notice_data.notice_contract_type
            notice_data.notice_text += l.find_element(By.CSS_SELECTOR,'div.card-header.bg-white').text
            l.find_element(By.CSS_SELECTOR,'#accordionLots > div:nth-child(n) > div.card-header.bg-white > div > div.col-2 > a > i').click()
            time.sleep(5)
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1

    except:
        pass
    try:
        WebDriverWait(page_main, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#modal-lots-title > button'))).click()
        time.sleep(5)
    except:
        pass
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.achats.defense.gouv.fr/marches-publics/appels-d-offres?type-search=region&type-cloture=none&date-debut=&date-fin=&q=&page=&sort=&segment=&currenttab=appel-offres&type-marches%5B%5D=appel-offres&type-marches%5B%5D=rfi&type-marches%5B%5D=programmation'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/section[2]/div/div/div[2]/div[2]/div[1]/div[1]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/section[2]/div/div/div[2]/div[2]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/section[2]/div/div/div[2]/div[2]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="tri"]/div[2]/nav/ul/li[4]/a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/main/section[2]/div/div/div[2]/div[2]/div[1]/div[1]'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
