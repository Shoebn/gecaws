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
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

external_link_list = []

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "it_aou"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'it_aou'
    
    notice_data.main_language = 'IT'
    
    notice_data.currency = 'EUR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.CorpoSx > div > ol > li > h3 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = 'Gare attive'
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.CorpoSx > div > ol > li> span").text
        publish_date = GoogleTranslator(source='it', target='en').translate(publish_date)         
        publish_date = publish_date.split('Publication:')[1].split(' -')[0]
        if 'th' in publish_date:
            publish_date=publish_date.replace('th','')
        elif 'st' in publish_date:
            publish_date=publish_date.replace('st','')  
        elif 'rd' in publish_date:
            publish_date=publish_date.replace('rd','')    
        elif 'nd' in publish_date:
            publish_date=notice_deadline.replace('nd','')
    
        try:
            publish_date = re.findall(' \w+ \d+ \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,' %B %d %Y').strftime('%Y/%m/%d')
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
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.CorpoSx > div > ol > li> span").text
        notice_deadline = GoogleTranslator(source='it', target='en').translate(notice_deadline)  
        notice_deadline = notice_deadline.split('Deadline:')[1].split('\n')[0] 
        if 'nd' in notice_deadline:
            notice_deadline=notice_deadline.replace('nd','')           
        elif 'st' in notice_deadline:
            notice_deadline=notice_deadline.replace('st','')  
        elif 'rd' in notice_deadline:
            notice_deadline=notice_deadline.replace('rd','')
        elif 'th' in notice_deadline:
            notice_deadline=notice_deadline.replace('th','')
        else:
            pass

        try:
            notice_deadline = re.findall(' \w+ \d+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,' %B %d %Y').strftime('%Y/%m/%d')
        except:
            notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d')
        
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'li > h3 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Azienda Ospedaliero-Universitaria di Modena'
        customer_details_data.org_phone = '02241740360'
        customer_details_data.org_country = 'IT'
        customer_details_data.org_address = 'Elenco delle caselle di posta elettronica certificata dell’Azienda Ospedaliero – Universitaria Sede legale: via del Pozzo 71 - 41124 Modena'
        customer_details_data.org_email = 'affarigenerali@pec.aou.mo.it'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > div.container.ContCorpoPag.contCorpo > div > div > div.ContCorpoPag.contCorpo > div.col-xs-12.col-sm-11.push_container > div.CorpoSx > div '):
            attachments_data = attachments()

            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'a').text.split('(')[1].split(')')[0]
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass

            try:
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass
            
            try:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                if 'pdf' in external_url:
                    attachments_data.file_type = 'pdf'
                elif 'doc' in external_url:
                    attachments_data.file_type = 'doc'
                elif 'docx' in external_url:
                    attachments_data.file_type = 'docx'
                elif 'xlsx' in external_url:
                    attachments_data.file_type = 'xlsx'         
                else:
                    pass


            except Exception as e:
                logging.info("Exception in external_url: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        
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
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
chrome_options = Options()
for argument in arguments:
    chrome_options.add_argument(argument)
page_main = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)
page_details = webdriver.Chrome(executable_path=ChromeDriverManager().install(), chrome_options=chrome_options)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.aou.mo.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/244'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[7]/div/div/div[1]/div[2]/div[1]/div[3]/ol/li[1]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[7]/div/div/div[1]/div[2]/div[1]/div/ol/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[7]/div/div/div[1]/div[2]/div[1]/div/ol/li')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[7]/div/div/div[1]/div[2]/div[1]/div[3]/ol/li[1]'),page_check))
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
    
