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
SCRIPT_NAME = "it_trasparenza"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'IT'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    notice_data.script_name = 'it_trasparenza'
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.titolo').text
        notice_data.notice_title = GoogleTranslator(source='it', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, " div.datibando > div:nth-child(2)").text.split('Categoria:')[1].split('\n')[0]
    except Exception as e:  
        logging.info("Exception in category: {}".format(type(e).__name__))
    
    try:
        estimated_amount = tender_html_element.find_element(By.CSS_SELECTOR, " div.datibando > div:nth-child(2)").text.split('Importo:')[1].split('\n')[0]
        est_amount = re.sub("[^\d\.\,]", "", estimated_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in estimated_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.blksotto > span').get_attribute("href")    
        n_url = 'https://trasparenza.aulss3.veneto.it'
        notice_data.notice_url = n_url + notice_url
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
        
    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.blk1.blk1_8.attivo').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > p').text
    except Exception as e:
        logging.info("Exception in local_description".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#container > div.rightside > div > div > div.pagina'))).get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure = page_details.find_element(By.XPATH, "//*[contains(text(),'Stato:')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in type_of_procedure: {}".format(type(e).__name__))
        pass
    
    customer_details_data = customer_details()
    customer_details_data.org_name = 'UOC Servizi Tecnici e Patrimoniali'
    customer_details_data.org_country = 'IT'
    try:
        customer_details_data.org_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimenti:")]//following::span').text
    except Exception as e:
        logging.info("Exception in org_description: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimenti:")]//following::td').text.split('Telefono: ')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in org_phone: {}".format(type(e).__name__))
        pass

    try:
        customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Riferimenti:")]//following::td').text.split('Email:')[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in org_email: {}".format(type(e).__name__))
        pass
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.ballegat'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a.spostatut').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' a.spostatut').get_attribute('href')
            attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'a.spostatut').text
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
       
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(2)'):
            tender_criteria_data = tender_criteria()
            tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, ' div.pagina > table > tbody > tr:nth-child(2) > td:nth-child(2)').text
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Data inizio:')]//following::td[1]").text
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)
        try:
            publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d')
            logging.info(notice_data.publish_date)     
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Data scadenza:')]//following::td[1]").text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)
        try:    
            notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d')
        except:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
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
    urls = ['https://trasparenza.aulss3.veneto.it/index.cfm?action=trasparenza.bandi'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[1]/div[4]/div[1]/div/div/div[3]/div[3]/a'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[1]/div[4]/div[1]/div/div/div[3]/div[3]/a')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[1]/div[4]/div[1]/div/div/div[3]/div[3]/a')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[1]/div[2]/div[1]/div/div/div[3]/div[3]/a[1]/div[1]'),page_check))
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
