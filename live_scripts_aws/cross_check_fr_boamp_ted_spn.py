from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_fr_boamp_ted_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_fr_boamp_ted_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    notice_data.script_name = 'fr_boamp_ted_spn'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    try:
        deadline_date = tender_html_element.find_element(By.CSS_SELECTOR, "#toplist > li > div h2 > p.fr-mb-2v.fr-mt-2v.ng-scope ").text
        deadline_date = GoogleTranslator(source='fr', target='en').translate(deadline_date)
        deadline_date = deadline_date.replace('.','').replace('at','')
        deadline_date = re.findall('\d+/\d+/\d{4}  \d+:\d{2} [ap][m]', deadline_date)[0]
        notice_data.notice_deadline = datetime.strptime(deadline_date,'%m/%d/%Y  %I:%M %p').strftime('%Y/%m/%d %H:%M:%S') 
        
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' p > a').get_attribute("href")
    except:
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' p > a').get_attribute("href")
    except:
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'p a').text
        notice_data.notice_title = GoogleTranslator(source='fr', target='en').translate(notice_data.local_title)
    except:
        pass
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'h2 div.fr-grid-row.fr-col-12.fr-col-sm-6 label').text.split('Avis n°')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass
        
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'li:nth-child(3) span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.type_of_procedure_actual =  tender_html_element.find_element(By.CSS_SELECTOR,'div.card-notification-info.fr-scheme-light-white.fr-p-2v.fr-pl-3v.fr-mb-1w > ul > li:nth-child(4) span:nth-child(2)').text
        type_of_procedure_actual = GoogleTranslator(source='fr', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_boamp_spn_procedure.csv",type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
                
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "h2 > div > div > div.fr-grid-row.fr-col-4.fr-col-sm-6.row-reverse-md").text
        publish_date = GoogleTranslator(source='fr', target='en').translate(publish_date)
        publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return  
        
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.boamp.fr/pages/recherche/?disjunctive.type_marche&disjunctive.descripteur_code&disjunctive.dc&disjunctive.code_departement&disjunctive.type_avis&disjunctive.famille&sort=dateparution&refine.type_avis=5&refine.type_avis=1&refine.type_avis=2&refine.type_avis=3&refine.type_avis=4&refine.famille=JOUE&q.filtre_etat=(NOT%20%23null(datelimitereponse)%20AND%20datelimitereponse%3E%3D%222023-06-22%22)%20OR%20(%23null(datelimitereponse)%20AND%20datefindiffusion%3E%3D%222023-06-22%22)"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        record_dropdwn_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.fr-btn.fr-btn--secondary.fr-fi-arrow-down-s-line.fr-btn--icon-right.colored-icon.fr-m-0.fr-px-3w.fr-text--sm.ng-binding')))
        page_main.execute_script("arguments[0].click();",record_dropdwn_clk)
        
        select_record_clk =  WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="dropdown-53242000"]/ul/li[3]/a')))
        page_main.execute_script("arguments[0].click();",select_record_clk)
        
        time.sleep(5)
        for page_no in range(2,50): #50
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#toplist > li > div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#toplist > li > div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#toplist > li > div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break
                
            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#toplist > li > div'),page_check))
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
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
