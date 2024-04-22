from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "de_ladadi_spn"
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
SCRIPT_NAME = "de_ladadi_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'de_ladadi_spn'
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.main_language = 'DE'
    
    notice_data.notice_type = 4
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'DE'
    notice_data.performance_country.append(performance_country_data)
    
    
    # Onsite Field -Angebotsfrist
    # Onsite Comment - grab both date and time 


    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text
        notice_deadline = notice_deadline.replace("\n",' ')
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Field -Beschreibung
    # Onsite Comment -just take title not url

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > p > strong').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Beschreibung
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > p > strong > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#readspeaker').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        
    # Onsite Field -HAD-Referenz-Nr
    # Onsite Comment -take notice no from tender page if present else split it from notice_url

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#c1380  div:nth-child(4)').text.split("HAD-Referenz-Nr.:")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    


    # Onsite Field -split data from "Leistungsbeschreibung" till "Leistungsort" dont take ref no -"HAD-Referenz-Nr"
    # Onsite Comment -None
    
    try:
        local_description = page_details.find_element(By.CSS_SELECTOR, '#c1380 > div').text.split("HAD-Referenz-Nr.:")[1].split("Leistungsort")[0].strip()
        local_description =  re.sub("\d+\/\d+","",local_description)
        notice_data.local_description = local_description.strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Ausführungszeit:')]//following::p[1]").text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass


    try:              
        customer_details_data = customer_details()
    # Onsite Field -Phone
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#c35407 > div > div:nth-child(3)').text.split("Telefon")[1].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#c35407 > div > div:nth-child(4) a').text.strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'DE'
        customer_details_data.org_language = 'DE'
        customer_details_data.org_parent_id = 7779226

        customer_details_data.org_name = 'Landkreises Darmstadt-Dieburg'
    # Onsite Field -Leistungsort:
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Leistungsort:')]//following::p[1]").text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        attach_url = page_details.find_element(By.CSS_SELECTOR, '#c1380 > div > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,attach_url,80)
        logging.info(attach_url)
    except Exception as e:
        logging.info("Exception in attach_url: {}".format(type(e).__name__))
        pass
    
    try:
        display_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ' button.gwt-Button.ANZEIGEN'))).click()
        time.sleep(2)
    except:
        pass
    
# Onsite Field -None
# Onsite Comment -click on the url for attachmwnts

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#activityPanel > div > div:nth-child(4) > div > div:nth-child(2) > div > div > div.activityPanelContainer > div > div:nth-child(2) > form > div > div:nth-child(3) > div > div:nth-child(2) > div > div > table > tbody > tr:nth-child(2) > td > table > tbody > tr > td > div > table > tbody > tr:nth-child(3) > td > fieldset > div > table > tbody > tr')[2::2]:
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -click on "display"," tr:nth-child(3) > td > fieldset > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > button"
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            attachments_data.file_name = file_name.split(".")[0].strip()

            external_url1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) button').click()
            time.sleep(5)

            external_url = page_details.find_element(By.CSS_SELECTOR, 'button.gwt-Button.GIVH1UACAK.GIVH1UACKK')
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

        # Onsite Field -ref url "https://www.subreport-elvis.de/browseVerdingungsunterlagen.html#ELVISID:E56877363"
        # Onsite Comment -click on "display"," tr:nth-child(3) > td > fieldset > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > button"


        # Onsite Field -None
        # Onsite Comment -click on "display"," tr:nth-child(3) > td > fieldset > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > button"

            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#activityPanel > div > div:nth-child(4) > div > div:nth-child(2) > div > div > div.activityPanelContainer > div > div:nth-child(2) > form > div > div:nth-child(3) > div > div:nth-child(2) > div > div > table > tbody > tr:nth-child(2) > td > table > tbody > tr > td > div > table > tbody > tr:nth-child(4) > td > fieldset > div > table > tbody > tr')[2::2]:
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -click on "display"," tr:nth-child(3) > td > fieldset > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > button"
            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            attachments_data.file_name = file_name.split(".")[0].strip()

            external_url1 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) button').click()
            time.sleep(5)

            external_url = page_details.find_element(By.CSS_SELECTOR, 'button.gwt-Button.GIVH1UACAK.GIVH1UACKK')
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

        # Onsite Field -ref url "https://www.subreport-elvis.de/browseVerdingungsunterlagen.html#ELVISID:E56877363"
        # Onsite Comment -click on "display"," tr:nth-child(3) > td > fieldset > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > button"


        # Onsite Field -None
        # Onsite Comment -click on "display"," tr:nth-child(3) > td > fieldset > div > table > tbody > tr:nth-child(2) > td:nth-child(4) > button"

            try:
                attachments_data.file_type = attachments_data.external_url.split(".")[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.notice_type) + str(notice_data.notice_url)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
page_details.maximize_window()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ladadi.de/nc/service/zentrale-auftragsvergabestelle/aktuelle-ausschreibungen.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="c1380"]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="c1380"]/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
    
            if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                break
        except:
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
    
