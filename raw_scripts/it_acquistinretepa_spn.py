#NOTE- after clicking on url >>> select "Altri Bandi"

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
SCRIPT_NAME = "it_acquistinretepa_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_acquistinretepa_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
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
    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -N.GARA
    # Onsite Field -also take notice_no from notice url


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
    
    # Onsite Field -ATTIVO DAL
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(8) > div > div.hidden-sm").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -AREA MERCEOLOGICA
    # Onsite Comment -None

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'div.nopadding.hidden-sm').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -SCADE IL
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(9) > div > div.hidden-sm").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding').text
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.cpv_at_source = 'CPV'
     
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa.col-sm-9.col-xs-12 > h5').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.titoloiniziativa.col-sm-9.col-xs-12 > h5').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Appalto di servizi - Service, Appalto di forniture - Supply

    try:
        notice_data.notice_contract_type = page_details.find_element(By.CSS_SELECTOR, 'div.vertical-align-inside-div-sm-md div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Appalto di servizi - Service, Appalto di forniture - Supply

    try:
        notice_data.contract_type_actual = page_details.find_element(By.CSS_SELECTOR, 'div.vertical-align-inside-div-sm-md div:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
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
    # Onsite Comment -click on "div.height-99-sm" >>>>> take multiple data i.e there are multiple tabs....following is the selector u can use "div.col-sm-10.pull-right"   ref url  -https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=6efc4d172366ab6a"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#all-page').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#all-page'):
            customer_details_data = customer_details()
        # Onsite Field -STAZ. APPALTANTE
        # Onsite Comment -None

            try:
                customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-12.col-lg-9.col-xs-12.nopadding > div:nth-child(3) > div > div > div:nth-child(6)').text
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
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'borderAB-left borderME-left'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -ref url -  "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=23f8c8da3e2989d0"

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.col-sm-4.col-xs-12.text-left.nopadding-sm.semibold-18').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -ref url -  "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=23f8c8da3e2989d0"

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div.nopadding.voffset > div').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -CIG
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div > div.col-sm-8 div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -CIG
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget = page_details.find_element(By.CSS_SELECTOR, 'div.borderR-sm.height80-sm.regular-16.ng-scope').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -CIG
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div.borderR-sm.height80-sm.regular-16.ng-scope').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.contract_type = page_details.find_element(By.CSS_SELECTOR, 'div.vertical-align-inside-div-sm-md div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.CSS_SELECTOR, 'div.vertical-align-inside-div-sm-md div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass




        # Onsite Field -None
        # Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=414410144912b091"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.ng-scope.borderAB-left'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -None
                    # Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=414410144912b091"

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'div.ng-scope.borderAB-left  div:nth-child(3) > div').text
			
                    # Onsite Field -None
                    # Onsite Comment -ref url - "https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=414410144912b091"

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'div.ng-scope.borderAB-left  div:nth-child(3) > div').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.margin-bottom-10-xs.height-99-sm > a > img'):
                    lot_cpvs_data = lot_cpvs()
		
                    # Onsite Field -None
                    # Onsite Comment -to get data --- click on "cpv" botton to grab data

                    lot_cpvs_data.lot_cpv_code = page_main.find_element(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding').text
			
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
			
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_at_source = page_main.find_element(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding').text
            except Exception as e:
                logging.info("Exception in lot_cpv_at_source: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                lot_details_data.lot_cpv_code = page_main.find_element(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding').text
            except Exception as e:
                logging.info("Exception in lot_cpv_code: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -CPV
# Onsite Comment -take data from CPV... ref url "https://www.acquistinretepa.it/opencms/opencms/scheda_bando.html?idBando=6efc4d172366ab6a"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-sm-12.col-lg-9.col-xs-12.nopadding > div'):
            cpvs_data = cpvs()
        # Onsite Field -CPV
        # Onsite Comment -click on "#categorie > button" to get data --- click on "cpv" botton to grab data

            try:
                cpvs_data.cpv_code = page_main.find_element(By.CSS_SELECTOR, 'div.col-sm-4.nopadding.ng-binding').text
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass
        
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -ref url - https://www.acquistinretepa.it/opencms/opencms/scheda_altri_bandi.html?idBando=237f17bd8cff12cc

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-xs-12.nopadding.col-lg-9 > div:nth-child(5)'):
            attachments_data = attachments()
        # Onsite Field -DOCUMENTAZIONE DI GARA
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div-text-left nopadding ng-scope').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -DOCUMENTAZIONE DI GARA
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div-text-left nopadding ng-scope').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -DOCUMENTAZIONE DI GARA
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div-text-left nopadding ng-scope').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


# Onsite Field -None
# Onsite Comment -ref url - "div.col-xs-12.nopadding > div > div:nth-child(7)"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-xs-12.nopadding.col-lg-9 > div:nth-child(5)'):
            attachments_data = attachments()
        # Onsite Field -DOCUMENTAZIONE DI GARA
        # Onsite Comment -None

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'div.nopadding.ellipsis > a > strong').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -DOCUMENTAZIONE DI GARA
        # Onsite Comment -None

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'div.nopadding.ellipsis > a > strong').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -DOCUMENTAZIONE DI GARA
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'div.nopadding.ellipsis > a > strong').get_attribute('href')
            
        
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
    urls = ["https://www.acquistinretepa.it/opencms/opencms/vetrina_bandi.html?filter=AB#!#post_call_position"] 
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
    