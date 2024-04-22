from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "my_rurallinkikku_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "my_rurallinkikku_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'my_rurallinkikku_spn'
    
    notice_data.main_language = 'MS'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MY'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
  
    notice_data.currency = 'MYR'
        
    notice_data.notice_url = url
    
    notice_data.notice_type = 4
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.column-norujukan').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, ' td.column-penerangan').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.column-tarikhterbitanbaru").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+ [AMPMampm]+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td.column-tarikhterbitan.sorting_1").text
            publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+ [AMPMampm]+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:   
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.column-tarikhtutupbaru.sorting_1").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+ [AMPMampm]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except:
        try:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.column-tarikhtutup").text
            notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+ [AMPMampm]+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline) 
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")                     
    except:
        pass
    
    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'MY'
        customer_details_data.org_language = 'MS'
        customer_details_data.org_name =  "KEMENTERIAN KEMAJUAN DESA DAN WILAYAH"
        customer_details_data.org_parent_id = 7813426
        
        try:
            customer_details_data.org_state = tender_html_element.find_element(By.CSS_SELECTOR, "td.expand.column-negeri").text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass 
    
    try:               
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, ' td.column-lampiran > a'):
            attachments_data = attachments()
            attachments_data.file_name = 'Tender Document'

            attachments_data.external_url = single_record.get_attribute("href")
            
            try:
                attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
            except:
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    formats = page_main.find_element(By.XPATH, '//*[@id="main"]/div[1]/section[2]/div/div/div/div/div').text
    if "IKLAN/TAWARAN" in  formats or "IKLAN/KENYATAAN KERJA UNDI" in formats:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.column-tajuk').text
            if len(notice_data.local_title) < 5:
                return
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
    elif "Iklan/Kenyataan Sebut Harga" in formats:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.column-penerangan').text
            if len(notice_data.local_title) < 5:
                return
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(30)
page_main.maximize_window()


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.rurallink.gov.my/tender-sebut-harga/iklan-tawaran-tender/","https://www.rurallink.gov.my/tender-sebut-harga/iklan-kenyataan-kerja-undi/","https://www.rurallink.gov.my/tender-sebut-harga/iklan-kenyataan-sebutharga/"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)  
          
        try:
            for page_no in range(2,8):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#table_1 > tbody > tr'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table_1 > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#table_1 > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#table_1 > tbody > tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
