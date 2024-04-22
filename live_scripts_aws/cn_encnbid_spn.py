from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_encnbid_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_encnbid_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
       
    notice_data.script_name = 'cn_encnbid_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Do take "New Tenders, Evaluation Results - 4 - SPN", "Evaluation Results Tenders Changes - 16	- AMD"

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'span.item-title-new').text
        if 'New Tenders' in notice_type:
            notice_data.notice_type = 4
        elif 'Tenders Changes' in notice_type:
            notice_data.notice_type = 16
        else:
            return
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.item-title-text.bold.fs18').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.derail-content > div').get_attribute("outerHTML")   
        notice_text = page_details.find_element(By.CSS_SELECTOR, 'div.derail-content > div').text
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '.item-title-text.bold.fs18').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass



    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.item-title.clearfix > span").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'span.item-title-new').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -None
    # Onsite Comment -split data from "Beginning of Selling Bidding Documents" till "Ending of Selling Bidding Documents"

    try:
        document_purchase_start_time = notice_text.split('Beginning of Selling Bidding Documents:')[1].split('\n')[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass

    # Onsite Field -None
    # Onsite Comment - split data from "Ending of Selling Bidding Documents" till "Sell bidding？"

    try:
        document_purchase_end_time = notice_text.split('Ending of Selling Bidding Documents:')[1].split('\n')[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = notice_text.split('Deadline for Submitting Bids/Time of Bid Opening (Beijing Time):')[1].split('\n')[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass
    try:
        notice_data.notice_no = notice_text.split('Bidding No:')[1].split('\n')[0]
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('/')[-1].split('-')[0]
        except Exception as e:
            logging.info("Exception in notice_type: {}".format(type(e).__name__))
            pass


    # Onsite Field -None
    # Onsite Comment - split data from "Price of Bidding Documents:" till "Additional Instructions".... take the value which is "CNY" eg..￥1000

    try:
        notice_data.document_cost = int(notice_text.split('Price of Bidding Documents:')[1].split('\n')[0].split('￥')[1].split('/')[0])
        
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass



    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Region
        # Onsite Comment -None

        try:
            org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'div.item-link > span:nth-child(2)').text.split('Region')[1]
            customer_details_data.org_city = GoogleTranslator(source='auto', target='en').translate(org_city)
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, '#bidding > div.derail-content > div > div.main-info').text.split('Purchasers:')[1].split('\n')[0]
        except:
            customer_details_data.org_name = page_details.find_element(By.CSS_SELECTOR, '#bidding > div.derail-content > div > div.main-info').text.split('Bidding Agency:')[1].split('\n')[0]
            
        
        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#bidding > div.derail-content > div > div.main-info').text.split('Add.:')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try: 
        
        notic_text = page_details.find_element(By.CSS_SELECTOR, 'div.derail-content > div').text
        if 'Products' in notic_text:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, ' div.derail-content > div > div.main-info > table > tbody > tr')[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_details_data.lot_actual_number=single_record.find_element(By.CSS_SELECTOR, ' tr:nth-child(n) > td:nth-child(1)').text
                except:
                    pass
                
                try:
                    lot_details_data.lot_quantity_uom=single_record.find_element(By.CSS_SELECTOR, ' tr:nth-child(n) > td:nth-child(3)').text
                except:
                    pass
                    
                try:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' tr:nth-child(n) > td:nth-child(2)').text
                    lot_details_data.lot_title_english = lot_details_data.lot_title
                except:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                    lot_details_data.lot_title_english = lot_details_data.lot_title

                
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        else:
            pass
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.chinabidding.com/en/info/search.htm'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bidding"]/div[3]/div/div[3]/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidding"]/div[3]/div/div[3]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bidding"]/div[3]/div/div[3]/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#pagerSubmitForm > li:nth-child(16) > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bidding"]/div[3]/div/div[3]/ul/li'),page_check))
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
    
