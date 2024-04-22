from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_yancheng_ca"
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
SCRIPT_NAME = "cn_yancheng_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cn_yancheng_ca'
    notice_data.main_language = 'ZH'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bt-left').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.bt-list-time.bt-right").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.bt-left').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
 
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#barrierfree_container').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -项目编号
    # Onsite Comment -split notice_no from ( Project number: or Item number: 	项目编号：) keyword

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, '#barrierfree_container').text.split('项目编号：')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CN'
        customer_details_data.org_language = 'ZH'
        
        # Onsite Field -None
        # Onsite Comment -split org_name from (Purchaser information	采购人信息  >>  Name   名称：) or  (Purchaser information  采购人信息  >>    name   名    称： ) or (Purchaser information	采购人信息  >>  Name 名 称：) or (Purchaser information	采购人信息  >>  Name   名  称：) keyword.    if possible

        try:
            org_name = page_details.find_element(By.CSS_SELECTOR, '#barrierfree_container').text
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name).split('Purchaser information')[1].split('Address')[0].split('Name:')[1]
        except Exception as e:
            customer_details_data.org_name = 'Yancheng City'
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -splir org_address from (Purchaser information	采购人信息  >> Address  地址： ) or (Purchaser information	采购人信息  >>  Address   地    址：) or  (Purchaser information	采购人信息  >>  Contact address:  联系人地址：) or (Purchaser information	采购人信息  >> Address  地  址： ) keyword.   if possible

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, '#barrierfree_container').text
            customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address).split('Purchaser information')[1].split('Address')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        notice_data.is_lot_default = True
        lot_details_data.lot_description = notice_data.notice_title
        try:
            award_details_data = award_details()
            
            # Onsite Field -None
            # Onsite Comment -split bidder_name from (Supplier Name:		供应商名称：) or (Winning bidder:	中标单位：) keywords.

            try:
                bidder_name = page_details.find_element(By.CSS_SELECTOR, '#barrierfree_container').text
                bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name)
                if 'Supplier Name:' in bidder_name:
                    award_details_data.bidder_name = bidder_name.split('Supplier Name:')[1].split('\n')[0]
                elif 'Winning bidder:' in bidder_name:
                    award_details_data.bidder_name = bidder_name.split('Winning bidder:')[1].split('\n')[0]
                else:
                    pass
            except Exception as e:
                logging.info("Exception in bidder_name: {}".format(type(e).__name__))
                pass
            
            # Onsite Field -None
            # Onsite Comment -split address from (Supplier Address:	供应商地址：) or (Address:	地址：) keywords.

            try:
                address = page_details.find_element(By.CSS_SELECTOR, '#barrierfree_container').text
                address = GoogleTranslator(source='auto', target='en').translate(address)
                if 'Supplier Address:' in address:
                    award_details_data.address = address.split('Supplier Address:')[1].split('\n')[0]
                elif 'Address:' in bidder_name:
                    award_details_data.address = address.split('Address:')[1].split('\n')[0]
                else:
                    pass
            except Exception as e:
                logging.info("Exception in address: {}".format(type(e).__name__))
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
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://czj.yancheng.gov.cn/col/col31690/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,4):#4
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div/div/div[2]/div/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div[2]/div/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div[2]/div/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'   tbody > tr > td:nth-child(8) > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div/div/div[2]/div/ul/li'),page_check))
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
