
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_ccgp_ca"
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
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_ccgp_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    notice_data.script_name = 'cn_ccgp_ca'
    notice_data.currency = 'CNY'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.main_language = 'ZH'
    notice_data.class_at_source = 'CPV'
    notice_data.document_type_description ='公开招标公告'
    
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "em:nth-child(2)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a').get_attribute("href") 
        fn.load_page(page_details,notice_data.notice_url,280)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"项目编号")]').text
        notice_data.notice_no = notice_no.split('项目编号：')[1].strip()
    except:
        notice_data.notice_no = notice_data.notice_url.split('_')[1].split('.')[0].strip()        
            
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.vF_detail_content_container > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    try:
        lot_number = 1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number
        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)   
        try:
            award_details_data = award_details()
            bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"供应商名称")]').text
            award_details_data.bidder_name = bidder_name.split('供应商名称：')[1].strip() 

            try:
                netawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"中标（成交）金额")]').text
                award_details_data.netawardvaluelc = float(netawardvaluelc.split('中标（成交）金额：')[1].split('（万元）')[0].strip())
            except Exception as e:
                logging.info("Exception in netawardvaluelc: {}".format(type(e).__name__))
                pass

            try:
                address = page_details.find_element(By.XPATH, '//*[contains(text(),"供应商地址")]').text
                award_details_data.address = address.split('供应商地址：')[1].strip()
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass      

            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass            

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
        lot_number += 1 
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass        
    
    customer_click = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"显示公告概要")]')))
    page_details.execute_script("arguments[0].click();",customer_click)
    logging.info("customer_click")
    notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div.vF_deail_maincontent').get_attribute("outerHTML")   

    try:
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'em:nth-child(4)').text
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"采购单位地址")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"项目联系人")]//following::td[1]').text 
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"项目联系电话")]//following::td[1]').text
            customer_details_data.org_phone = re.findall('\d{3}-\d+',org_phone)[0]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"行政区域")]//following::td[1]').text 
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
    
    try:             
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.table > table > tbody > tr > td > a'):
            attachments_data = attachments()
            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.file_name = single_record.text
            try:
                attachments_data.file_type = attachments_data.file_name.split('.')[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass    


    notice_data.identifier = str(notice_data.script_name)  +  str(notice_data.local_description) + str(notice_data.notice_type) +  str(notice_data.notice_url) 
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

page_main = uc.Chrome()
page_details = uc.Chrome()

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.ccgp.gov.cn/cggg/zygg/zbgg/"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.vF_detail_relcontent_lst > ul > li:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.vF_detail_relcontent_lst > ul > li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.vF_detail_relcontent_lst > ul > li')))[records]   
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
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.vF_detail_relcontent_lst > ul > li:nth-child(1)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.vF_detail_relcontent_lst > ul > li:nth-child(1)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except Exception as e:
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
            
    