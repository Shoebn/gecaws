# NOTE ---Use VPN for the URL

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_ospedale_spn"
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
import gec_common.th_Doc_Download as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_ospedale_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    notice_data.script_name = 'it_ospedale_spn'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.procurement_method = 2
    notice_data.currency = 'EUR'
    notice_data.document_type_description = 'Bandi di gara e contratti'

    try:
        try:
            title = tender_html_element.find_element(By.CSS_SELECTOR, '#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot   p:nth-child(1) > span').text
            title = title.lower()
            if title.startswith('avviso esplorativo di manifestazione di interesse'):
                notice_data.notice_type = 5
            else:
                notice_data.notice_type = 4
        except:
            pass
        
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot   p:nth-child(1) > span').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > p:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return    

    try:  
        notice_deadline1 = tender_html_element.find_element(By.CSS_SELECTOR,"#ctl00_cphBody_mcsInternoElencoBandi_pnlSlot  div >  p:nth-child(3) > span").text
        if 'ORE' in notice_deadline1 or 'ore' in notice_deadline1:
            try:
                notice_deadline = re.findall('\d+/\d+/\d{4} [ORE:|ore]+ \d+:\d+:\d+',notice_deadline1)[0]
                try:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ORE: %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ore %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_deadline = re.findall('\d+/\d+/\d{4} [ORE:|ore|ora locale]+ \d+:\d+',notice_deadline1)[0]
                try:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ORE: %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ore %H:%M').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y ora locale %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        else:
            notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline1)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass     
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        customer_details_data = customer_details()
        customer_details_data.org_name = 'L’Azienda Ospedaliera di Perugia'
        customer_details_data.org_parent_id = '1322722'
        customer_details_data.org_phone = '075 5781'
        customer_details_data.org_email = 'acquistiappalti.aosp.perugia@postacert.umbria.it'
        customer_details_data.org_address = 'sant andrea delle frattle - 06129 PERUGIA'
        customer_details_data.org_language = 'IT'
        customer_details_data.org_country = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass  

    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')

# ----------------------------------------- Main Body

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ospedale.perugia.it/pagine/bandi-di-gara-e-contratti"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_main.find_element(By.XPATH,'//button[contains(text(),"Accetta")]').click()
        except:
            pass
        time.sleep(2)
        for page_no in range(2,20):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div')))[records]
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
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_no))))
                page_main.execute_script("arguments[0].click();", next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="ctl00_cphBody_mcsInternoElencoBandi_pnlSlot"]/div/div[1]/div'), page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:" + str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
