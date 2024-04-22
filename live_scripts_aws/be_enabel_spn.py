#NOTE - for details click on "+" symbol on right top corner of each tender record

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "be_enabel_spn"
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
SCRIPT_NAME = "be_enabel_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'FR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.script_name = 'be_enabel_spn'
    
    click = tender_html_element.click()
    time.sleep(5)
    
    try:
        WebDriverWait(tender_html_element, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.card--news.card--tenders.\|.font-normal.group.text-inherit.min-w-full.col-span-12.bg-white.no-underline.open > div > p:nth-child(2) > strong')))
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -map it with "be_enabel_spn_all_countrycode"
    
    try:
        performance_country_data = performance_country()
        p_country = tender_html_element.find_element(By.CSS_SELECTOR, 'div.news__botton > p:nth-child(2)').text.split("Country :")[1].strip()
        performance_country_data.performance_country = fn.procedure_mapping("assets/be_enabel_spn_all_countrycode.csv",p_country)

    
        if performance_country_data.performance_country is None or performance_country_data.performance_country=='':
            performance_country_data.performance_country = 'BE'
            notice_data.performance_country.append(performance_country_data)
        else:
            notice_data.performance_country.append(performance_country_data)
        
    except:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -None
    # Onsite Comment -take the number which is before the title, before the "dash""-" as "notice .no"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#news p.h5 > span').text.split("– ")[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -take the data which is after the "dash""-" as "local_title"

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#news p.h5 > span').text.split("– ")[1].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -closing date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.news__botton > p:nth-child(3)").text
        notice_deadline = re.findall('\d+ \w+ \d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    try:
        notice_data.local_description = tender_html_element.text.split("Description :")[1].split("Attachments :")[0].split("Lien à suivre pour la réunion d’information:")[0].strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass


    
    # Onsite Field -None
    # Onsite Comment -description is not present in each record grab the data where it is present.... split data from "description" till "attachments
    
    notice_data.notice_url = 'https://www.enabel.be/public-procurement/'
    
    try:
        notice_data.notice_text += tender_html_element.find_element(By.XPATH, '//*[@id="news"]/div[2]/div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'ENABEL'
        customer_details_data.org_parent_id = '7476190'
    # Onsite Field -Country
    # Onsite Comment -None

        try:
            customer_details_data.org_country = performance_country_data.performance_country 
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'FR'


        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field - None
# # Onsite Comment - attachment are not present in each tender record "just select attachments" .....  split data from "attachments"

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR,' p:nth-child(n) > a'):
            attachments_data = attachments()

            attachments_data.external_url = single_record.get_attribute('href')

            try:
                attachments_data.file_name = single_record.text.split(".")[0].strip()
            except:
                attachments_data.file_name = 'Tender Document'
        
            try:
                attachments_data.file_type = single_record.text.split(".")[1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.enabel.be/public-procurement/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            pop_up = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"]'))).click()
        except:
            pass
        
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="news"]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="news"]/div[2]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
