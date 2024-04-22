#NOTE - there are multiple tender table present take data from all those table ... following are the table header"(All kinds of Naval Stores including General Store, Clothing Store, Office Equipment, Software, etc ),"( All kinds of Aviation, IT Provider, Equipment, Generator, Engines and related Spare Parts, etc )","( All kinds of Food Items, Crockeries Cutleries, Vehicle and Vehicle Spare/Repair etc ).

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bd_nssd_spn"
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
from selenium.webdriver.common.action_chains import ActionChains
import selenium.webdriver.common.keys
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bd_nssd_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'bd_nssd_spn'
    notice_data.currency = 'BDT'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BD'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.main_language = 'EN'
    notice_data.notice_type = 4
    
    # Onsite Field -Tender Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > p').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -QTY
    # Onsite Comment -None

    try:
        notice_data.tender_quantity = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > p').text
    except Exception as e:
        logging.info("Exception in tender_quantity: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opening Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6) > p").text
        notice_deadline = re.findall('\d+.\d+.\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
        
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
        
    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'
        attachments_data.file_description = 'Tender Document'
        attachments_data.file_type = 'pdf'
    # Onsite Field -Spec
    # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7) a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    
    # Onsite Field -Notice
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,100)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        

    page_details.switch_to.window(page_details.window_handles[0])
    time.sleep(5)
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > table > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

    # Onsite Field -Tender Publication Date
    # Onsite Comment -None

    try:
        publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Publication Date')]//following::span[1]").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'BD'
        customer_details_data.org_name = 'Naval Stores Sub Depot Dhaka Limited'
        customer_details_data.org_parent_id = '7481936'

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '''//*[contains(text(),'Tel. No.')]//following::td[1]''').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, '''//*[contains(text(),'Fax. No.')]//following::td[2]''').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '''//*[contains(text(),'E-mail')]//following::td[3]''').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '''//*[contains(text(),'Name & Address of the office (s):')]//following::td[1]''').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > formfeed > table > tbody > tr'):
            single_record_data = single_record.text
            if single_record_data != '':
                
                lot_details_data = lot_details()
            
        # Onsite Field -Item
        # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        # Onsite Field -Ser
        # Onsite Comment -None

                lot_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                lot_details_data.lot_number = int(lot_number)

        # Onsite Field -Remarks
        # Onsite Comment -None

                try:
                    lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Deno
        # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Delivery time after issue of w/order	
        # Onsite Comment -None

                try:
                    lot_details_data.contract_duration  = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

        # Onsite Field -Qty
        # Onsite Comment -None

                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_details_data.lot_quantity = float(lot_quantity)
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass
        
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    time.sleep(2)

    
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
    urls = ["https://nssd.navy.mil.bd/0/0/front-tender"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[4]/div/div/div[2]/div/table/tbody/tr')))[records]
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
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
