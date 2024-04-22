from gec_common.gecclass import *
import logging
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
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "in_nddb_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'INR'
    notice_data.main_language = 'EN'
    notice_data.script_name = 'in_nddb_ca'
    notice_data.notice_type = 7
    
    
    notice_data.notice_url =url
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__)) 
        pass
    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__)) 
        pass    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
       
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_data.publish_date = datetime.strptime(publish_date, '%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__)) 
        pass 

    
    try:
        procument_method = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(10)').text
        if 'Local' in procument_method:
            notice_data.procurement_method = 0
        elif 'International' in procument_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except:
        pass

    try:
        notice_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(8)').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'NATIONAL DAIRY DEVELOPMENT BOARD'
        customer_details_data.org_parent_id = '6971886'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        
        try:
            award_details_data = award_details()
            try:
                award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
            except Exception as e:
                logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                pass
            
            try:
                grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(7)').text
                try:
                    grossawardvaluelc = grossawardvaluelc.split('Rs.')[1]
                    grossawardvaluelc = grossawardvaluelc.replace(',','')
                except:
                    pass
                if '/-' in grossawardvaluelc:
                    grossawardvaluelc = grossawardvaluelc.split('/-')[0]
                award_details_data.grossawardvaluelc = float(grossawardvaluelc)
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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

    urls = ['http://tenders.nddb.coop/SitePages/ContractAwardDetails.aspx?hash=l5HE28NqphYFZBmWXQ0EiOe8JcvJunclCJTLy%2Bqqaat2drpby3JPla6LUTl1lsag',
           'http://tenders.nddb.coop/SitePages/ContractAwardDetails.aspx?hash=%2FlBDzTuz31SDmYB0zmVKTwkmFwtUpagE0x8LN8B0aYw%3D',
           'http://tenders.nddb.coop/SitePages/ContractAwardDetails.aspx?hash=SGZcuvyJgUXRTVpr76aW%2BdtvBz2OmvS34sQsgO2xQA8%3D'] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
            
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_m_g_401eb54b_3b19_41bb_809e_87fde5c11198 > table > tbody > tr:nth-child(2) > td > table.tableTitleBg > tbody > tr')))
            length = len(rows) 
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#ctl00_m_g_401eb54b_3b19_41bb_809e_87fde5c11198 > table > tbody > tr:nth-child(2) > td > table.tableTitleBg > tbody > tr')))[records]
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
