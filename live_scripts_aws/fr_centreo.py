
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_centreo"
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
SCRIPT_NAME = "fr_centreo"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'fr_centreo'
    notice_data.main_language = 'FR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.resultatOrganismeMilieu > p').text  
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div> div.resultatOrganismeBasTab4 > p").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR, "div> div.resultatOrganismeBasTab4 > p").text.split("\n")[1]
        notice_time = re.findall("\d+",notice_deadline1)
        notice_time1 = " ".join(notice_time)
        notice_date=notice_deadline+" "+notice_time1
        notice_data.notice_deadline = datetime.strptime(notice_date,'%d/%m/%Y %H %M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    if  notice_data.notice_deadline is None:
        return
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.resultatOrganismeBasTab2 > p > a:nth-child(1)').get_attribute("href")     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_no = notice_data.notice_url.split('marche_public_')[1].split('.html')[0]
        notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' #didomi-notice-agree-button'))).click()
    except:
        pass
    time.sleep(2)
    
    try:
        holder = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tabs-vert')))
    except:
        pass
    time.sleep(5)

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#tabs-vert').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text = tender_html_element.get_attribute("outerHTML")  
    
    text = notice_data.notice_text
    try:
        if '<br><span><i>Type de procédure : </i>' in text and '.</span><br>' in text:
            notice_data.type_of_procedure_actual = text.split('<br><span><i>Type de procédure : </i>')[1].split('.</span><br>')[0]                    
        elif '<br><span><i>Type de procédure : </i>' in text and '</span><br>' in text:
            notice_data.type_of_procedure_actual = text.split('<br><span><i>Type de procédure : </i>')[1].split('</span><br>')[0]
        
        elif 'Type de procédure :</i>' in text and '</span><br>' in text:
            type_of_procedure_actual = text.split('Type de procédure :</i>')[1].split('</span><br>')[0]      
            notice_data.type_of_procedure_actual = type_of_procedure_actual.split(', ')[0]
              
        elif 'Type de procédure :<br>\n' in text and '<br>' in text:
            type_of_procedure_actual = text.split('Type de procédure :<br>\n')[1].split('<br>')[0]      
            notice_data.type_of_procedure_actual = type_of_procedure_actual.split(', ')[0]
            
        elif 'ProcédureType de procédure :' in text and 'ouverteCondition de participation' in text:
            notice_data.type_of_procedure_actual = text.split('ProcédureType de procédure :')[1].split('ouverteCondition de participation')[0]  

        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        type_of_procedure = type_of_procedure.capitalize()
        notice_data.type_of_procedure = fn.procedure_mapping('assets/fr_centreo_procedure.csv',type_of_procedure)   

    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
            
    try:
        local_description = page_details.find_element(By.CSS_SELECTOR, '#onglet1 > div.div_e.div_e-bottom > div').text       
        if len(local_description)< 1:
            pass
        else:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, '#onglet1 > div.div_e.div_e-bottom > div').text 
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type de marché : ")]').text.split("Type de marché :")[1].split("\n")[0].strip() 
        if "Travaux" in notice_contract_type or "travaux" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Services" in notice_contract_type or "services" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Fournitures" in notice_contract_type or "fournitures" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Autre" in notice_contract_type or "autre" in notice_contract_type:
            notice_data.notice_contract_type = "Non consultancy"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.resultatOrganismeHaut').text
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.centreofficielles.com/recherche_marches_publics_aapc_____25072023_26072023_1.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(2)
        try:
            Accepter_et_fermer_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' #didomi-notice-agree-button'))).click() 
        except:
            pass
        time.sleep(25)
        
        todays_date = date.today()
        todays_date = todays_date.strftime('%d/%m/%Y')

        au_clear_click  = page_main.find_element(By.XPATH,"(//input[contains(@class,'hasDatepicker')])[2]").clear()
        au_send_date_click  = page_main.find_element(By.XPATH,"(//input[contains(@class,'hasDatepicker')])[2]").send_keys(todays_date)
        rechercher_click  = page_main.find_element(By.XPATH,'//*[@class="rechercher"]').click()
        time.sleep(2)

        try:
            for page_no in range(2,12):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="contenuOrganisme2"]/div[2]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contenuOrganisme2"]/div[2]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="contenuOrganisme2"]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultats-cerca-avancada"]/app-resultats-cerca-avancada/div'),page_check))
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
    
