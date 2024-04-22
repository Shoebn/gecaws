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
SCRIPT_NAME = "fr_marches"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'fr_marches'

    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'

    notice_data.procurement_method = 2

    notice_data.notice_type = 4


    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.date.date-min.clearfix").text.strip()
        publish_date = publish_date.replace('\n',' ')
        if '.' in publish_date:
            publish_date = publish_date.replace('.','')
        
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        if ',' in publish_date:
            publish_date = publish_date.replace(',','')

        try:
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d')
        except:
            try:
                notice_data.publish_date = datetime.strptime(publish_date,'%b %d %Y').strftime('%Y/%m/%d')
            except:
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d %Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
        notice_data.notice_contract_type = GoogleTranslator(source='auto', target='en').translate(notice_contract_type)       
        if 'Supplies' in notice_data.notice_contract_type:   
            notice_data.notice_contract_type = 'Supply'
        elif 'Public Works' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Services' in notice_data.notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
                        
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul.list-unstyled > li:nth-child(1) > a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.m-b-10').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.CSS_SELECTOR, "#collapseHeading > div.panel-body > div > div > div:nth-child(1) > div > span > span").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Référence :")]//following::div[1]').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Intitulé :")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = notice_data.local_description
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#panelPieces > ul > li a'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')   
            attachments_data.file_name = single_record.text.split('-')[0].strip()
            try:
                file_size = single_record.text.split('-')[1].strip()
                attachments_data.file_size = GoogleTranslator(source='fr', target='en').translate(file_size)
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
     
    try:              
        customer_details_data = customer_details()

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organisme :")]//following::span[1]').text  
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            page_details.find_element(By.CSS_SELECTOR,"#collapseHeading > div.panel-heading.clearfix > h1").click()   
            time.sleep(3)
        except:
            pass

        try:
            customer_details_data.org_city = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'li:nth-child(2) > ul > li:nth-child(3) > div'))).text 
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_click = page_details.find_element(By.CSS_SELECTOR,"ul > li:nth-child(2) > div > span > a").get_attribute('href')
        lot_click = lot_click.split("popUpSetSize(")[1].split("'")[1]
        lot_page_url = 'https://www.marches-publics.gouv.fr'+ lot_click
        fn.load_page(page_details1,lot_page_url,80)  
        lot_number = 1
        for single_record in page_details1.find_elements(By.XPATH, '/html/body/form/div[5]/div/div/div/div[2]/div'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            try:
                lot_title = single_record.find_element(By.CSS_SELECTOR, '#headingOne > span').text
                lot_details_data.lot_title = GoogleTranslator(source='auto', target='en').translate(lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                lot_details_data.lot_title = notice_data.notice_title

            collapese = single_record.find_element(By.CSS_SELECTOR,'#headingOne').click()
            time.sleep(2)

            try:
                lot_details_data.lot_description = single_record.find_element(By.XPATH,'div[2]/div/div[2]/div').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                lot_details_data.lot_description = notice_data.notice_summary_english

            try:
                contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text   
                lot_details_data.contract_type = GoogleTranslator(source='auto', target='en').translate(contract_type)
                
                if 'Supplies' in lot_details_data.contract_type:   
                    lot_details_data.contract_type = 'Supply'
                elif 'Public Works' in lot_details_data.contract_type:
                    lot_details_data.contract_type = 'Works'
                elif 'Services' in lot_details_data.contract_type:
                    lot_details_data.contract_type = 'Service'
                else:
                    pass
                
            except Exception as e:      
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            
            try:
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, "//*[contains(text(),'CPV')]//following::div[1]/span[1]").text.split('(')[0].strip()
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in cpv_code: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(4) > div > span').text.split('(')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    try:
        type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(6) > div').text
        type_of_procedure_actual = GoogleTranslator(source='fr', target='en').translate(type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_marches_procedure.csv",type_of_procedure_actual) 
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(5) > div').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
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
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.marches-publics.gouv.fr/?page=Entreprise.EntrepriseAdvancedSearch&searchAnnCons"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            page_main.find_element(By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche").click()            
        except:
            pass
        
        for page_no in range(1,222):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div[2]/div[2]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,"//i[contains(@class,'fa fa-angle-right')]"))) 
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div[2]/div[2]'),page_check))
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
