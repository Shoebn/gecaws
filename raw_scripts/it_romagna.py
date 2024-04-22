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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_romagna"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'it_romagna'
    
    notice_data.main_language = 'IT'
        
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(n) > h2 > a > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    try:
        notice_data.type_of_procedure=tender_html_element.find_element(By.CSS_SELECTOR, "div > h2 > span").text
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass        
    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass


    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.bandoDates > span:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.bandoDates > span:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div> h2 > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Stato procedura')]//following::span[1]").text
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.contextualbody > div>p:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#allegati > ul'):
            attachments_data = attachments()
 
            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, '#allegati > ul > li > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, '#allegati > ul > li > span').text.split('(')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, '#allegati > ul > li > a').get_attribute("href")
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#portal-column-content >div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        est_amount = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(4)').text.split('Importo appalto')[1].split('€')[0]
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        document_opening_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Apertura busta amministrativa')]//following::span[1]").text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y/%m/%d')                                                                                               
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
       
        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.bandoEnte  span:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

      
        try:
            clk = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cc-banner"]/div/div/div[3]/a[2]')))
            page_details.execute_script("arguments[0].click();",clk)
        except:
            pass
    
        try:
            page = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,'Referenti'))).click()
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, ' li:nth-child(1) > div > div:nth-child(1) > a').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'ul > li:nth-child(1) > div > div:nth-child(2) > span').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Responsabile del procedimento")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:
        page = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.LINK_TEXT,'CIG'))).click()
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        try:
            lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#listacig > ul > li > b').text
            lot_details_data.lot_title  = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
        except:
            lot_details_data.lot_title = notice_data.notice_title

        try:
            lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#listacig > ul > li').text.split('CIG:')[1]
        except Exception as e:
            logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
            pass
    
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:              
        tender_criteria_data = tender_criteria()
        tender_criteria_data.tender_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'p:nth-child(5)').text.split('Criterio di aggiudicazione')[1]
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        notice_data.document_type_description = 'Bandi Altri Enti - aperti'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    


    # Onsite Comment -use below new url for below format  :- https://intercenter.regione.emilia-romagna.it/servizi-imprese/consultazioni-preliminari-di-mercato/consultazioni-aperte
    
    
    notice_data.document_type_description = 'Consultazioni aperte'
    
    # Onsite Field -None
    # Onsite Comment -format 2

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > h2').text
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.documentByLine").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
     
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_deadline = 'take as threshold'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div> h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#portal-column-content >div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#portal-column-content >div'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'Regione Emilia Romagna'
            customer_details_data.org_parent_id = '7669631'
            customer_details_data.org_country = 'IT'
            customer_details_data.org_language = 'IT'

        # Onsite Field -CONTATTI
        # Onsite Comment -take in textform 

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),'CONTACTS')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

        # Onsite Field -CONTATTI
        # Onsite Comment -take only email

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),'CONTACTS')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
 

# Onsite Field -None
# Onsite Comment -take only when attachment if available 

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),'Allegati')]//following::a[1]'):
            attachments_data = attachments()
        # Onsite Field -Allegati
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),'Allegati')]//following::a[1]').get_attribute('href')
            
        
        # Onsite Field -Allegati
        # Onsite Comment -take in textform

            try:
                attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),'Allegati')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Allegati
        # Onsite Comment -take only size
            try:
                attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),'Allegati')]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
        

    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ['https://intercenter.regione.emilia-romagna.it/servizi-imprese/bandi-altri-enti/bandi-altri-enti-aperti?b_start:int=0'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,7):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="content-core"]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-core"]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="content-core"]/div[2]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' nav:nth-child(2) > ul > li.next > a')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="content-core"]/div[2]/div'),page_check))
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
    
