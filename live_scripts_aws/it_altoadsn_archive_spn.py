from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "it_altoadsn_archive_spn"
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
SCRIPT_NAME = "it_altoadsn_archive_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
  
    notice_data.script_name = 'it_altoad_archive_spn'
    notice_data.main_language = 'IT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    notice_data.notice_type = 4
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Tipo di bando o avviso speciale
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.pad-btm-10px.truncate > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data pubblicazione:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.pad-btm-20px > div:nth-child(2) > span:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data scadenza:
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.pad-btm-20px > div:nth-child(3) > span:nth-child(2)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split tender number from the data --- eg "S000555/2023 | "   S000554
    # Onsite Comment -if the notice number is missing from the tender use following selector to grab "tender no"    CUP---"div.pad-btm-35px.pad-top-15px.pad-left-15px > div:nth-child(2) > span:nth-child(2)",  CIG - "div.pad-btm-35px.pad-top-15px.pad-left-15px > div:nth-child(1) > span:nth-child(2)"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.font-s.links.pad-btm-10px.cursor-pointer.truncate > span').text.split('|')[0].strip()
        notice_data.tender_id = notice_data.notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.font-s.links.pad-btm-10px.cursor-pointer.truncate > span').text.split('|')[0].replace('/','-').strip()
        notice_data.notice_url = 'https://www.bandi-altoadige.it/notice/special-notice/'+notice_url+'/resume'
        fn.load_page(page_details1,notice_data.notice_url,120)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
      
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'div.content-panel > special-notice-details').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    
    try:
        notice_data.local_description = page_details1.find_element(By.CSS_SELECTOR, 'div.f-s-13px.pad-top-10px').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        pass
               
    try:
        notice_data.local_title = page_details1.find_element(By.CSS_SELECTOR, 'div > span > span:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
    # Onsite Field -split  data till "dash" "-" symbol .......... the data which is before dash take it as org name
    # Onsite Comment -eg "PROVINCIA AUTONOMA DI BOLZANO - 17.5 - UFFICIO AGGIORNAMENTO E DIDATTICA"  -- " PROVINCIA AUTONOMA DI BOLZANO > take  as org name"

        customer_details_data.org_name = page_details1.find_element(By.CSS_SELECTOR, 'notice-details > div > div > div > h2.f-s-13px').text.split('-')[0].strip()

    # Onsite Field -split  data till "dash" "-" symbol .......... the data which is after dash take it as org address
    # Onsite Comment -eg "PROVINCIA AUTONOMA DI BOLZANO - 17.5 - UFFICIO AGGIORNAMENTO E DIDATTICA"  -- " UFFICIO AGGIORNAMENTO E DIDATTICA > take  as org address"
        try:
            org_address = page_details1.find_element(By.CSS_SELECTOR, 'notice-details > div > div > div > h2.f-s-13px').text
            if '-' in org_address and '-' in org_address:
                customer_details_data.org_address = org_address.split('-')[2].strip()
            else:
                customer_details_data.org_address = org_address.split('-')[1].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_main_activity = page_details1.find_element(By.CSS_SELECTOR, 'h2.f-s-13px').text.split('-')[1].strip()
        except:
            pass

    # Onsite Field -RUP
    # Onsite Comment -None
    
        try:
            customer_details_data.contact_person = page_details1.find_element(By.CSS_SELECTOR, 'rup-autocomplete > div > div.form-element.f-s-13px > span').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -DOCUMENTAZIONE ALLEGATA
# Onsite Comment -None

    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.box-content.pad-20px.collapsible-content > div > div div:nth-child(3)'):
            attachments_data = attachments()
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div > div > a').text.split('.')[-1].strip()
            except:
                pass
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div > h3').text
            try:
                attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'div>div>span:nth-child(4)').text.split(':')[1]
            except:
                pass

            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div > div > a")))
            external_url.location_once_scrolled_into_view
            external_url.click()
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = (str(file_dwn[0]))

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details1 = Doc_Download.page_details 
 
try:
    th = date.today() - timedelta(1)
    threshold = '2022/01/01'
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bandi-altoadige.it/notice/special-notice/list"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        page_main.find_element(By.CSS_SELECTOR,'i.icon.fa.fa-chevron-down').click()
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="search-direct-order-publishedAtFrom"]/input').send_keys('01/01/2022 00:00')
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="search-direct-order-publishedAtTo"]/input').send_keys('01/01/2024 00:00')
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="search-direct-order-publishedAtTo"]/input').click()
        time.sleep(3)

        for page_no in range(1,20):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/div[2]/special-notice-list/div[2]/special-notice-item-list/div/ul/li'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[2]/special-notice-list/div[2]/special-notice-item-list/div/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/div[2]/special-notice-list/div[2]/special-notice-item-list/div/ul/li')))[records]
                extract_and_save_notice(tender_html_element)

            try:   
                next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/div[2]/special-notice-list/div[2]/div[3]/paginator-bottom/div/button[2]')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/div[2]/special-notice-list/div[2]/special-notice-item-list/div/ul/li'),page_check))
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
    page_details1.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)