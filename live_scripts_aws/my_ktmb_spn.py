from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "my_ktmb_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "my_ktmb_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'my_ktmb_spn'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MY'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 4
    
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'MYR'
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DESCRIPTION
    # Onsite Comment -None

    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -RFQ NUMBER
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -LAST DATE TO PURCHASE
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    if notice_data.local_title is '':
            return
    # Onsite Field -SUBMISSION CLOSING DATE
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -RFQ PRICE (RM)
    # Onsite Comment -None
    try:
        document_cost = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        document_cost = re.sub("[^\d\.\,]","",document_cost)
        notice_data.document_cost=float(document_cost)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DETAILS
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(10) > center > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#customers').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'KERETAPI TANAH MELAYU BERHAD (KTMB)'
        customer_details_data.org_parent_id = '7209625'
        customer_details_data.org_country = 'MY'
        customer_details_data.org_language = 'EN'
        # Onsite Field -RFQ BRIEFING
        # Onsite Comment -None

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#     this below field were missing from our side kindly add the below code 
#customers > tbody
    try:
        for t in page_details.find_elements(By.CSS_SELECTOR, '#customers > tbody'):
            data= t.text
            if "ITEM DESCRIPTION QUANTITY" in data:
                lot_number = 1
                for single_record in t.find_elements(By.CSS_SELECTOR, '#customers > tbody > tr')[1:]:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

            # Onsite Field -ITEM DESCRIPTION
            # Onsite Comment -just take "lot_title" from the table

                    lot_title = single_record.text.split(" ")[2:-2]
                    lot_details_data.lot_title =",".join(lot_title)
                    lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            # Onsite Field -ITEM NUMBER
            # Onsite Comment -just take "lot_actual_number" from the table

                    try:
                        lot_actual_number = single_record.text.split(" ")[1].strip()
                        lot_details_data.lot_actual_number = re.findall('\d{2}-\d{4}-\d{1}-\d+',lot_actual_number)[0]
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass
                    # Onsite Field -QUANTITY
                # Onsite Comment -None
                    try:
                        lot_details_data.lot_quantity = float(single_record.text.split(" ")[-2].strip())
                    except Exception as e:
                        logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                        pass

                # Onsite Field -UOM
                # Onsite Comment -None
                    try:
                        lot_details_data.lot_quantity_uom = single_record.text.split(" ")[-1].strip()
                    except Exception as e:
                        logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                        pass        
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
page_main = webdriver.Chrome(options=options)

time.sleep(20) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://form.ktmb.com.my/eproc/eProc/index.php?module=weba&cat=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
