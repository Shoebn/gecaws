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
import functions as fn
from functions import ET
NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_mofcom"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.notice_type = 4

    notice_data.main_language = 'ZH'
    
    notice_data.currency = 'CNY'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.script_name = 'cn_mofcom'

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " div.tit_04.mt20.pp > span").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date : {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.source_of_funds = tender_html_element.find_element(By.CSS_SELECTOR, ' div.txt_06 > span:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in source_of_funds : {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#infoList  div.tit_04.mt20.pp > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, 'h1#bulletinName').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if 'Bidding Announcement' or 'Tender Announcement' in notice_data.notice_title :
            notice_data.procurement_method= 1
        elif 'National Competitivie Bidding' in notice_data.notice_title :
            notice_data.procurement_method= 0
        else:
            notice_data.procurement_method= 2
        notice_data.notice_summary_english = notice_data.notice_title
       
    except Exception as e:
        logging.info("Exception in local_title : {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, ' div.txt_05 > a').text.split(",")[0]
    except Exception as e:
        logging.info("Exception in notice_no : {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text = page_details.find_element(By.CSS_SELECTOR, 'body > section > div > div.mt20.clearfix').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text : {}".format(type(e).__name__))
        pass
    
    try:
        notice_text = page_details.find_element(By.XPATH, '/html/body/section/div/div[2]/div[2]').text
    except:
        try:
            notice_text = page_details.find_element(By.XPATH, '/html/body/section/div/div[2]/div[2]/p').text
        except:
            pass
            
    try:
        notice_deadline = notice_text.split('投标截止时间')[1].split("\n")[0]
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline : {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        try: 
            org_name = notice_text.split("招标人: ")[1].split("\n")[0]
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
        except:
            try:
                org_name = notice_text.split("招标人:")[1].split("\n")[0]
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            except:
                customer_details_data.org_name = "Ministry of Commerce of the People's Republic of China"

            
        if '招标人：北京遥感设备研究所' in notice_text:
            org_name = '北京遥感设备研究所'
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            
        try:
            org_address = notice_text.split('地址: ')[1].split("\n")[0]
            customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
        except:
            try:
                org_address = notice_text.split('地址:')[1].split("\n")[0]
                customer_details_data.org_address = GoogleTranslator(source='auto', target='en').translate(org_address)
            except Exception as e: 
                logging.info("Exception in org_address : {}".format(type(e).__name__))
                pass
            
        try:
            customer_details_data.org_phone = notice_text.split("联系方式: ")[1].split("\n")[0]
        except:
            try:
                customer_details_data.org_phone = notice_text.split("联系方式:")[1].split("\n")[0]
            except Exception as e: 
                logging.info("Exception in org_phone : {}".format(type(e).__name__))
                pass
        customer_details_data.org_country = 'CN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details : {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.document_fee = page_details.find_element(By.CSS_SELECTOR, ' div.mt20.clearfix > div.article').text.split("招标文件售价:")[1].split("\n")[0]
    except Exception as e:
        logging.info("Exception in document_fee : {}".format(type(e).__name__))
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'li.files'):
            attachments_data = attachments()
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute("href")  
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments : {}".format(type(e).__name__)) 
        pass
    
    try:
        document_purchase_start_time = notice_text.split('招标文件领购开始时间:')[1].split("\n")[0]
        document_purchase_start_time = re.findall('\d{4}-\d+-\d+',document_purchase_start_time)[0]                                
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.document_purchase_start_time)
    except Exception as e:
        logging.info("Exception in document_purchase_start_time : {}".format(type(e).__name__))
        pass
    
    try:
        document_purchase_end_time = page_details.find_element(By.CSS_SELECTOR, 'div.mt20.clearfix > div.article').text.split("招标文件领购结束时间:")[1].split("\n")[0]
        document_purchase_end_time = re.findall('\d{4}-\d+-\d+',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%Y-%m-%d').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time : {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['http://chinabidding.mofcom.gov.cn/channel/business/bulletinList.shtml'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,10):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="infoList"]/li'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="infoList"]/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="infoList"]/li')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="infoList"]/li'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
