from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ae_dewa_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

#Note:Open tha site than click on "Document details ▽ " dropdown button than grab tha data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
clk_index = 1
SCRIPT_NAME = "ae_dewa_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global clk_index
    notice_data = tender()

    notice_data.script_name = 'ae_dewa_spn'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AE'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AED'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_url = url
    # Onsite Field -None
    # Onsite Comment -Note:If in this "div:nth-child(4) > div > div > dl > dd:nth-child(6)" selector have this keyword "Extended" than take notice_type "16" other wise it will be "4"
    
    Tender_Status = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div > dl > dd:nth-child(6)').text
    if 'Extended' in Tender_Status:
        notice_data.notice_type = 16
    else:
        notice_data.notice_type = 4
    # Onsite Field -None
    # Onsite Comment -Note:Take only numatic  value

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div > dl > dd:nth-child(2)').text.split('View')[0].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tender Description:
    # Onsite Comment -Note:Take data after "Tender Description" this keyword in local_title

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div > dl > dd:nth-child(4)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'DUBAI ELECTRICITY AND WATER AUTHORITY (DEWA)'
        customer_details_data.org_parent_id = '7520154'
        customer_details_data.org_country = 'AE'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
    # Onsite Field -Tender No
    # Onsite Comment -None
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > dl > dd:nth-child(2) > a').text

    # Onsite Field -Tender No
    # Onsite Comment -None

        external_url = tender_html_element.find_element(By.CSS_SELECTOR, "div > div > dl > dd:nth-child(2) > a").click()
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        time.sleep(5)
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -Tender Fee(Dhs)
    # Onsite Comment -Note:Splite after "Tender Fee(Dhs)" this keyword
    try:
        button_clk = tender_html_element.find_element(By.CSS_SELECTOR, 'button.m37-expander__trigger.m37-expander__trigger--themed').click()
        time.sleep(2)
    except:
        pass
    try:
        test_data = page_main.find_element(By.XPATH, '(//div[@class="m37-expander__content m37-expander__content--open"])'+'['+str(clk_index)+']' ).text
    except:
        pass
    
    try:
        notice_data.document_fee = test_data.split('Tender Fee(Dhs):')[1].split('Floating Date:')[0].strip()
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass

    # Onsite Field -Floating Date
    # Onsite Comment -Note:Splite after "Floating Date" this keyword

    try:
        publish_date = test_data.split('Floating Date:')[1].split('Closing Date:')[0].strip()
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    

    # Onsite Field -Closing Date
    # Onsite Comment -Note:Splite after "Closing Date" this keyword

    try:
        notice_deadline = test_data.split('Closing Date:')[1].split('Buying Details:')[0].strip()
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    clk_index += 1
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
page_main.maximize_window()
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.dewa.gov.ae/en/supplier/services/list-of-tender-documents"] 
    for url in urls:
        fn.load_page(page_main, url, 80)
        logging.info('----------------------------------')
        logging.info(url)
        page_main.refresh()

        try:
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rs_area"]/div/div/div[4]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="rs_area"]/div/div/div[4]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
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
