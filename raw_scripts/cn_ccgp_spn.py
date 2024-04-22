

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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_ccgp_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'cn_ccgp_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'CNY'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'ZH'
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.vF_detail_relcontent_lst  li > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div > blockquote').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -项目概况 / Project Overview
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div > blockquote').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -项目概况 / Public bidding announcement
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_relcontent.mt13 > h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -split data from "预算金额/Budget amount" till "最高限价（如有)/Maximum price"
    # Onsite Comment -None

    try:
        notice_data.est_amount = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from "预算金额/Budget amount" till "最高限价（如有)/Maximum price"
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -发布时间
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "em:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -split from "售价" till "提交投标文件截止时间"........... just  take amount
    # Onsite Comment -None

    try:
        notice_data.document_fee = tender_html_element.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split from "合同履行期限" till "本项目"
    # Onsite Comment -None

    try:
        notice_data.document_fee = tender_html_element.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.vF_detail_relcontent_lst li > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.vF_detail_content_container > div'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -split data from "地址" till "联系方式"

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'em:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -split data from "地址" till "联系方式"

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -split data from "联系方式 /Contact information"

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'CN'
            customer_details_data.org_language = 'ZH'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref url "http://www.ccgp.gov.cn/cggg/zygg/gkzb/202310/t20231019_20906452.htm"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.vF_detail_content_container > div > table'):
            lot_details_data = lot_details()
        # Onsite Field -ref url "http://www.ccgp.gov.cn/cggg/zygg/gkzb/202310/t20231019_20906452.htm"
        # Onsite Comment -包号 / serial number

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container  tr:nth-child(2) > td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url "http://www.ccgp.gov.cn/cggg/zygg/gkzb/202310/t20231019_20906452.htm"
        # Onsite Comment -标的名称 / Subject name

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container  tr:nth-child(2) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url "http://www.ccgp.gov.cn/cggg/zygg/gkzb/202310/t20231019_20906452.htm"
        # Onsite Comment -数量 / quantity

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container  tr:nth-child(2) > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -ref url "http://www.ccgp.gov.cn/cggg/zygg/gkzb/202310/t20231019_20906452.htm"
        # Onsite Comment -简要技术需求或服务要求 / Brief technical needs or service requirements

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container  tr:nth-child(2) > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["http://www.ccgp.gov.cn/cggg/zygg/gkzb/index.htm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,40):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="detail"]/div[2]/div/div[1]/div/div[2]/div[1]/ul/li'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    