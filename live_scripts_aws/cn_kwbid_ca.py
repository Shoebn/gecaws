from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_kwbid_ca"
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
SCRIPT_NAME = "cn_kwbid_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'cn_kwbid_ca'
    
    notice_data.main_language = 'ZH'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.ny_wzlb > ul > li > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
  
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.xxy_nr').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.zzy_sj").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
  
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'div.xxy_bt').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = "Procurement Results Announcement"
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english=notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    try:
        notice_no = page_details.find_element(By.CSS_SELECTOR, 'div.xxy_bt').text
        if '（' in notice_no:
            notice_data.notice_no=notice_no.split('（')[1].split('）')[0]  
        else:
            pass
        logging.info(notice_data.notice_no)
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:                       
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Guangxi Kewen Tendering and Consulting Co. Ltd.'
        customer_details_data.org_parent_id = 7797602
        customer_details_data.org_country = 'CN'
        customer_details_data.org_email = 'kwzbzfcg@126.com'
        customer_details_data.org_phone = '0771-2023972'
        customer_details_data.org_fax = '0771-2023971'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass


    try:
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.xxy_nr'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = notice_data.notice_title
            lot_details_data.lot_description = notice_data.notice_title
            notice_data.is_lot_default = True
            try:
                bidder_name = page_details.find_element(By.CSS_SELECTOR, 'div.xxy_nr').text
                if "供应商名称" in bidder_name:
                    award_details_data = award_details()
                    bidder_name=page_details.find_element(By.XPATH, '//*[contains(text(),"供应商名称")]//following::span[1]').text   
                    award_details_data.bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name)
                    try:
                        address = page_details.find_element(By.CSS_SELECTOR, 'div.xxy_nr').text
                        award_details_data.address = fn.get_string_between(address,'供应商地址：','成交金额')
                        award_details_data.address = GoogleTranslator(source='auto', target='en').translate(award_details_data.address)
                    except Exception as e:
                        logging.info("Exception in address: {}".format(type(e).__name__))
                        pass

                elif "主选中标人" in bidder_name:
                    award_details_data = award_details()
                    bidder_name1=page_details.find_element(By.CSS_SELECTOR, 'body > div.wrap > div.ggxxy > div.xxy_nr > div.xxy_text > div > table > tbody > tr:nth-child(3) > td:nth-child(2)').text   
                    award_details_data.bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name1)
                    try:
                        address = page_details.find_element(By.CSS_SELECTOR, 'div.xxy_nr').text
                        award_details_data.address=fn.get_string_between(address,'供应商地址：','成交金额')
                        award_details_data.address= GoogleTranslator(source='auto', target='en').translate(award_details_data.address)
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
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["http://www.kwbid.com.cn/newslist.jsp?id=5"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[6]/div[2]/div[2]/div[1]/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[6]/div[2]/div[2]/div[1]/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[6]/div[2]/div[2]/div[1]/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[6]/div[2]/div[2]/div[1]/ul/li'),page_check))
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
