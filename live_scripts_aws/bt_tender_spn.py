from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bt_tender_spn"
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
SCRIPT_NAME = "bt_tender_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'bt_tender_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BT'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BTN'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    # Onsite Field -Status
    # Onsite Comment -Note:If this select start with "Contract Awarded"than take notice_type=7 or if start "Being processed"than take notice_type=4 or if start "Live" than take notice_type=4 or if start "Amendment Issued" than take notice_type=16.

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(5)').text
        if "Contract Awarded" in notice_type:
            notice_data.notice_type = 7
        elif "Being processed" in notice_type or "Live" in notice_type:
            notice_data.notice_type = 4
        else:
            notice_data.notice_type = 16
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Name,Tender ID
    # Onsite Comment -Note:Splite befor ","

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(1)').text.split(",")[0].strip()
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Deadline
    # Onsite Comment -Note:Grab date and time also

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        notice_deadline = re.findall('\d+ \w+, \d{4} \d+:\d{2}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %b, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return
    
    # Onsite Field -Status
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -Note:Repleace  following  keywords  with  given  keywords("Civil=Works","Services=Service","Goods=Supply")
    
    # Onsite Field -Category
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual= tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        if "Civil" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tender Name,Tender ID
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
   
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div.main-section').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Tender Name,Tender ID
    # Onsite Comment -Note:Splite after ","    .Note:If notice_no is blank than take from url in page_detail

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text.split(",")[1].strip()
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = re.findall('\d{8}',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    
    # Onsite Field -EARNEST MONEY DEPOSIT DETAILS >> EMD Type
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.XPATH, '//*[contains(text(),"EMD Type")]//following::p[1]').text.split("EMD Value: ")[1].strip()
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    

    try:              
        tender_criteria_data = tender_criteria()
    # Onsite Field -EVALUATION DETAILS
    # Onsite Comment -Note:Splite befor this ":"

        tender_criteria_data.tender_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Evaluation Details")]//following::p[1]').text.split(":")[0].strip()

    # Onsite Field -EVALUATION DETAILS
    # Onsite Comment -Note:Splite after ":"

        tender_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Evaluation Details")]//following::p[1]').text.split(":")[1].strip()
        tender_criteria_weight = re.sub("[^\d\.\,]","",tender_criteria_weight)
        tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
        tender_criteria_data.tender_criteria_cleanup()
        notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Procuring Agency
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text

    # Onsite Field -Dzongkhag/Location
    # Onsite Comment -Note:Splite after "Dzongkhag/Location" this keyworg

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, ' div.page_content > div:nth-child(3) > div:nth-child(1) > p:nth-child(2)').text.split("Dzongkhag/Location:")[1].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'BT'
        customer_details_data.org_language = 'EN'           
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.page_content table:nth-child(7) tr ')[1:]:
            attachments_data = attachments()
        # Onsite Field -Document
        # Onsite Comment -None

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            # Onsite Field -Link
            # Onsite Comment -None


            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(3) a').get_attribute('href')
        
            attachments_data.file_type = attachments_data.external_url.split(".")[-1]

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
# Ref_url=https://tender.bt/ten23120003
    try:   
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.page_content  table:nth-child(15) tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Item Code
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Item Name
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
        
        # Onsite Field -UoM
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Qty
        # Onsite Comment -None

            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

        # Onsite Field -Category
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div:nth-child(3) > table:nth-child(11) > tbody > tr')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Item Code
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -Item Name
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            lot_details_data.lot_title_english =GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)

        # Onsite Field -UoM
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass

        # Onsite Field -Qty
        # Onsite Comment -None

            try:
                lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

        # Onsite Field -Category
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tender.bt/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="active-tenders"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="active-tenders"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="active-tenders"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="active-tenders"]/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
