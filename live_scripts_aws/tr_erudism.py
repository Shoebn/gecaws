from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "tr_erudism"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "tr_erudism"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global row_number
    notice_data = tender()
    
    notice_data.script_name = 'tr_erudism'
    
    notice_data.main_language = 'TR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'TRY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    
    try:
        notice_data.notice_url = page_main.find_element(By.XPATH, '/html/body/div[1]/section[2]/div/div/div[1]/article/table/tbody/tr['+str(row_number)+']/td[2]/a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Konusu")]//following::td[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Konusu")]//following::td[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    try:
        deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Tarihi")]//following::td[1]').text
        deadline = re.findall('\d+/\d+/\d{4}',deadline)[0]
        notice_data.notice_deadline = datetime.strptime(deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    
    try:
        publish = page_details.find_element(By.XPATH, '//*[contains(text(),"İlan Tarihi")]//following::td[1]').text
        publish = re.findall('\d+/\d+/\d{4}',publish)[0]
        notice_data.publish_date = datetime.strptime(publish,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.sayfaicerigi.test').get_attribute("outerHTML")                     
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Erciyes Üniversitesi Tıp Fakültesi Hastaneleri'
        customer_details_data.org_address = 'Döner Sermaye İşletme Müdürlüğü TALAS YOLU ÜZERİ KÖŞK MAH. PROF. DR. TURHAN FEYZİOĞLU CAD. (BİNA 14 K BLOK 1. KAT) 38030 - MELİKGAZİ / KAYSERİ'
        customer_details_data.org_phone = '+90 352 437 49 20 / +90 352 437 69 34'
        customer_details_data.org_fax = '+ 90 352 437 52 88'
        customer_details_data.org_email = 'satinalma1@erciyes.edu.tr'
        customer_details_data.org_parent_id = '7768775'

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Ekleyen")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.file_name = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Dosyası")]//following::td[1]').text.split('(')[0].replace(" ",'')

        try:
            attachments_data.file_type = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Dosyası")]//following::td[1]').text
            if('.pdf' in attachments_data.file_type):
                attachments_data.file_type = 'pdf'
            elif('.doc' in attachments_data.file_type):
                attachments_data.file_type = 'doc'
            else:
                attachments_data.file_type = attachments_data.file_type
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
    
        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Dosyası")]//following::a[1]').get_attribute('href')
        
        try:
            attachments_data.file_size = page_details.find_element(By.XPATH, '//*[contains(text(),"İhale Dosyası")]//following::td[1]').text.split('Dosya Boyutu: ')[1].split(")")[0]
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    row_number += 1
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
    urls = ['https://erudsim.erciyes.edu.tr/Guncel-Ihaleler/1/1/Guncel-Ihaleler.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="movies"]/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="movies"]/tr')))
                length = len(rows)
                row_number = 2
                for records in range(1,20):
                    extract_and_save_notice(records)
                    if notice_count >= MAX_NOTICES:
                        break
            
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="vergino"]/div[2]/a[5]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(10)
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="movies"]/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
