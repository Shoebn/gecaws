from gec_common.gecclass import *
import logging
import re,time
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from gec_common.web_application_properties import *

title_head = ['LONG TEXT','ITEM DESCRIPTION','MATERIAL DESCRIPTION','NUPCO DESCRIPTION','NUPCO Description',
                  'ITEM SPECIFICATION','Short Description','Description','DESCRIPTION','Long Item Description',
                  'MATERIAL DESCRIPTION','FINAL LONG TEXT','ITEM LONG DESCRIPTION','MATERIAL LONG DESCRIPTION',
                  'LONG DESC','SHORT TEXT','Item Description','ITEM NAME','Item Description ']

quantity_head = ['Quantity','INITIAL QUANTITY','QUANTITY','Initial Qty','Total QTY','QTY','Final QUANTITY','Final Total QTY','Total','MODA INITIAL QTY','Final Quantities','Nedded QTY']

lot_quantity_uom_head = ['UOM','SRM UOM','OUM','UNIT','UOM2','Unit']

lot_actual_number_head = ['SRM CODE','NUPCO CODE','SRM Code','NUPCO Code','NUPCO CODE2',' Item Code ','Product']

bidder_name_head = ['VENDOR NAME','Vendor Name']

bidder_country_head = ['COUNTRY','Country']

award_quantity_head = ['Final Quantity','Final Quantities','Quantitiy','Final Quantity ة!ئاهنلا تا!مᝣلا']

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_sa_nupco_ca"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    notice_data.script_name = 'sa_nupco_ca'
    notice_data.main_language = 'AR'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.currency = 'SAR'
    notice_data.procurement_method = 2
    
    notice_type = tender_html_element.find_element(By.CSS_SELECTOR,'p.box_arbic_text_p').text
    if 'النتائج النهائية' in notice_type:
        notice_data.notice_type = 7
    else:
        return
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.box.box_arbic  div.box_arbic_col01').text.split("رقم المنافسة")[1].replace('\n','')
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > p:nth-child(2)').text  
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.column-box.mix div > a').get_attribute("href") 
        logging.info(notice_data.notice_url)                    
    except:
        notice_data.notice_url = url
        
    notice_data.notice_text += tender_html_element.get_attribute("outerHTML") 
    notice_data.publish_date = threshold
    
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
    urls = ["https://nupco.com/%d8%a7%d9%84%d9%85%d9%86%d8%a7%d9%81%d8%b3%d8%a7%d8%aa/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Container"]/div')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="Container"]/div')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    logging.info("Exception:"+str(e))
    raise e
    
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
