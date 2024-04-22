from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_salute_spn"
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
import re
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_salute_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'it_salute_spn'

    notice_data.main_language = 'IT'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'

    notice_data.procurement_method = 2

    notice_data.currency = 'EUR'

    notice_data.notice_type = 4

    
    if url==urls[0]:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'p.titolo').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Data pubblicazione:
        # Onsite Comment -None

        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "p:nth-child(3)").text
            publish_date= GoogleTranslator(source='auto', target='en').translate(publish_date)
            try:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')    
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        logging.info(notice_data.publish_date)  

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        # Onsite Field -Data scadenza
        # Onsite Comment -None

        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "p:nth-child(4)").text
            notice_deadline= GoogleTranslator(source='auto', target='en').translate(notice_deadline)
            try:
                notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]                
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S') 
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass
            
        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'p.titolo > a').get_attribute("href")                     
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url

    else:
        
        try:
            notice_data.local_title = tender_html_element.text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        try:
            notice_data.notice_url = tender_html_element.get_attribute("href")   
            fn.load_page(page_details,notice_data.notice_url,80)
            logging.info(notice_data.notice_url)
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            notice_data.notice_url = url
            
        notice_text=WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH,'//*[@id="main-content"]'))).text

        # Onsite Field -Data pubblicazione:
        # Onsite Comment -None

        try:
            publish_date = notice_text.split('Data di pubblicazione:')[1].split('\n')[0]
            publish_date= GoogleTranslator(source='auto', target='en').translate(publish_date)
            try:
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                publish_date = re.findall('\w+ \d+, \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')    
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass
        logging.info(notice_data.publish_date)  

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return


        
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
    
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.salute.gov.it/portale/documentazione/p6_2_7.jsp?lingua=italiano&concorsi.page=0",
           "https://www.salute.gov.it/portale/ministro/p4_10_1_1_atti_1.jsp?lingua=italiano&btnCerca="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        if url==urls[0]:
            try:
                WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,'Chiudi'))).click()
            except:
                pass

            for page_no in range(2,40):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="page-content"]/div[2]/div[2]/div/div[1]/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-content"]/div[2]/div[2]/div/div[1]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="page-content"]/div[2]/div[2]/div/div[1]/ul/li')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="page-content"]/div[3]/div[2]/div/div[1]/ul/li'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        else:
            for page_no in range(2,40):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'dt a'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'dt a')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'dt a')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#page-content > div:nth-child(3) > div.span8.portlet-right.top-selector > div.portlet-content.ricerca-opuscoli > div:nth-child(1) > dl'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
                
    logging.info("Done cross checked total notice which has to be downloaded {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
    
