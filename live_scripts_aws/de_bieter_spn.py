from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_bieter_spn"
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
import gec_common.Doc_Download_ingate as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "de_bieter_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'de_bieter_spn'

    notice_data.main_language = 'DE'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.document_type_description = 'Öffentliche Verfahren'

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.color-primary.card-title-style').text 
        notice_data.notice_title = GoogleTranslator(source='de', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div:nth-child(1) > label').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div:nth-child(2) > label').text
        if 'Sicherungsleistung/bauaffine Dienstleistung' in notice_contract_type or 'Dienstleistung' in notice_contract_type:
            notice_data.notice_contract_type='Service'
        elif 'Bauleistung' in notice_contract_type:
            notice_data.notice_contract_type=' Works'
        elif 'Lieferleistung' in notice_contract_type:
            notice_data.notice_contract_type='Supply'
        elif 'Architekten- und Ingenieurleistungen' in notice_contract_type:
            notice_data.notice_contract_type='Consultancy'
        else:
            pass 
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,"div:nth-child(2) > div:nth-child(1) > label").text     
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        tender_html_element.find_element(By.CSS_SELECTOR,"div.button-area-style > button > span.mat-button-wrapper > span").click()
        time.sleep(10)
        notice_data.notice_url = page_main.current_url   
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'project-details > div > div:nth-child(2)'))).get_attribute("outerHTML")        
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        type_of_procedure_actual = page_main.find_element(By.CSS_SELECTOR, "div > div:nth-child(12) > div:nth-child(2)").text  
        if 'EU:' in type_of_procedure_actual:
            notice_data.type_of_procedure_actual = type_of_procedure_actual.split('EU: ')[1]
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/de_bieteri_spn_procedure.csv",type_of_procedure)
        else:
            notice_data.type_of_procedure_actual=type_of_procedure_actual
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/de_bieteri_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::div[1]').text 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Beschreibung")]//following::div[1]').text  
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english) 
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Bekanntmachung")]//following::div[1]').text
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y, %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        
        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, 'mat-card-content > div > div:nth-child(4) > div:nth-child(2)').text 
    
        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresse")]//following::div[1]').text 
        except Exception as e: 
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_city = page_main.find_element(By.CSS_SELECTOR, 'div > div:nth-child(14) > div:nth-child(2)').text  
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        cpvs_code = page_main.find_element(By.XPATH,'//*[contains(text(),"Klassifizierung")]//following::div[1]').text
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass

    try:                      
        attachments_data = attachments()
        attachments_data.file_name = 'tender documents'
        attachments_data.file_type = 'zip'
        external_url = page_main.find_element(By.XPATH, '/html/body/app/supplier-portal-frame/div/div/mat-sidenav-container/mat-sidenav-content/project-details/div/div[1]/button[2]').click()
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        back_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'nav > ol > li:nth-child(1) > a')))
        page_main.execute_script("arguments[0].click();",back_clk)
        WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div[1]')))
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://bieterportal.noncd.db.de/evergabe.bieter/eva/supplierportal/portal/tabs/vergaben'] 
    for url in urls:
        fn.load_page(page_main, url, 180)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            page_main.find_element(By.XPATH, '//*[@id="mat-dialog-0"]/shared-notification-message-dialog/mat-dialog-actions/button').click()
        except:
            pass
        
        try:
            entries_per_page = WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-select-6"]/div/div[2]/div')))
            page_main.execute_script("arguments[0].click();",entries_per_page)
        except Exception as e:
            logging.info("Exception in entries_per_page: {}".format(type(e).__name__)) 
            pass
        
        try:
            entries_per_page_value = WebDriverWait(page_main, 180).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#mat-option-10 > div')))
            page_main.execute_script("arguments[0].click();",entries_per_page_value)
        except Exception as e:
            logging.info("Exception in entries_per_page_value: {}".format(type(e).__name__)) 
            pass

        time.sleep(5)
        #---------------------------
        scheight = .1

        while scheight < 9.9:
            page_main.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            scheight += .01

        time.sleep(2)

        try:
            page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.XPATH,'//*[@id="project-vertical-container"]/div'))).text
            rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="project-vertical-container"]/div')))[records]  
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
    
