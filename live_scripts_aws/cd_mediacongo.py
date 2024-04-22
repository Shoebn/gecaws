
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cd_mediacongo"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cd_mediacongo"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cd_mediacongo_spn'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CD'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'CDF'
    notice_data.main_language = 'FR'
    notice_data.procurement_method = 2
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > a > strong').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass   
    
    try:
        notice_type_text = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text        
        if 'Extension de date' in notice_type_text or 'Modifié' in notice_type_text or "AVIS D'ANNULATION" in notice_type_text:   
            notice_data.notice_type = 16
            notice_data.script_name = 'cd_mediacongo_amd'
        elif 'ATTRIBUTION DE MARCHE' in notice_type_text:
            notice_data.notice_type = 7
            notice_data.script_name = 'cd_mediacongo_ca'
        else:
            notice_data.notice_type = 4
            notice_data.script_name = 'cd_mediacongo_spn'
    except Exception as e:
        logging.info("Exception in notice_type_text: {}".format(type(e).__name__))
        pass         
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_no = re.findall('\w+\d+', notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass           
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return     
    
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML')     
      
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.more_hemploi_left.articles_lleft').get_attribute("outerHTML")    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url      

    try:
        notice_deadline = page_details.find_element(By.XPATH, '(//*[contains(text(),"Date de publication")])[2]').text
        notice_deadline = notice_deadline.split('Date de clôture :')[1].split('(')[0]
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline = notice_deadline.replace('at ','')
        if 'p.m.' in notice_deadline:
            notice_deadline = notice_deadline.replace('p.m.','pm')
        else:
            notice_deadline = notice_deadline.replace('a.m.','am')
        notice_deadline = re.findall('\w+ \d+, \d+ \d+:\d+ [apAP][mM]', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%B %d, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass          

    try:
        document_opening_time = page_details.find_element(By.XPATH, '(//*[contains(text(),"Date de publication")])[2]').text
        document_opening_time = document_opening_time.split('Ouverture des offres')[1].split('(')[0]
        document_opening_time = GoogleTranslator(source='auto', target='en').translate(document_opening_time)
        document_opening_time = re.findall('\w+ \d+, \d+', document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time, '%B %d, %Y').strftime('%Y-%m-%d')  
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass          

    try:              
        customer_details_data = customer_details()
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        
        customer_details_data.org_country = 'CD'
        customer_details_data.org_language = 'FR'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass        
    
    try:              
        attachments_data = attachments()

        attachments_data.file_name = 'Tender Document' 
        attachments_data.file_description = 'Tender Document'

        try:
            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'body > div.more_harticles > div.more_hemploi_left.articles_lleft > div:nth-child(13) > p > span > strong > a').get_attribute('href')   
        except:
            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'body > div.more_harticles > div.more_hemploi_left.articles_lleft > div:nth-child(13) > p > span > strong > span > a').get_attribute('href')    
        try:
            attachments_data.file_type = attachments_data.external_url.split('.')[-1]
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass          

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.mediacongo.net/appels.html"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            for page_no in range(1,9):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table > tbody > tr:nth-child(2)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr')))[records] 
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                        if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                            break
                        if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                            logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                            break
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.pagination > div > a:nth-child(2) > img')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    page_check2 = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table > tbody > tr:nth-child(2)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table > tbody > tr:nth-child(2)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except Exception as e:
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
                    