from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_yancheng_spn"
log_config.log(SCRIPT_NAME)
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
SCRIPT_NAME = "cn_yancheng_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'CNY'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.script_name = 'cn_yancheng_spn'
    
    notice_data.main_language = 'ZH'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

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
    
#     # Onsite Field -None
#     # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span").text
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

#     # Onsite Field -None
#     # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(2)').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -(Contract number:	合同编号：)
#     # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'span#contractCode').text
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH,"/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr/td/table[3]/tbody").text.split('合同编号：')[1].split('\n')[0]
        
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

# # Onsite Field -None
# # Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#barrierfree_container > table > tbody > tr > td > div > div > table.bt-content.zoom.clearfix'):
            customer_details_data = customer_details()
#         # Onsite Field -(Purchaser (Party A):	采购人（甲方）：)
#         # Onsite Comment -None

            try:
                org_name = single_record.find_element(By.CSS_SELECTOR, 'span#htbuyerName').text
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            except:
                org_name = page_details.find_element(By.XPATH,"/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr/td/table[3]/tbody").text.split('采购人（甲方）：')[1].split('\n')[0]
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)

        
#         # Onsite Field -(Contact information:	联系方式：)
#         # Onsite Comment -None

            try:
                customer_details_data.org_phone = single_record.find_element(By.CSS_SELECTOR, 'span#buyerPhone').text
            except:
                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH,"/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr/td/table[3]/tbody").text.split('联系方式：')[1].split('\n')[0]
                                    
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
        
#         # Onsite Field -(Address: 		地址：)
#         # Onsite Comment -None

            try:
                org_address = single_record.find_element(By.CSS_SELECTOR, 'span#buyerAddress').text
                customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
            except:
                try:
                    org_address = page_details.find_element(By.XPATH,"/html/body/table[2]/tbody/tr/td/table[2]/tbody/tr/td/table[3]/tbody").text.split('地 址：')[1].split('\n')[0]
                    customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)                
                except Exception as e:
                    logging.info("Exception in org_address: {}".format(type(e).__name__))
                    pass
        
            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
    urls = ["http://czj.yancheng.gov.cn/col/col20137/index.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10): #10
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'li.clearfix.bt-list-new'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.clearfix.bt-list-new')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'li.clearfix.bt-list-new')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' tr > td:nth-child(8) > a')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'li.clearfix.bt-list-new'),page_check))
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
