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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "kh_gdpp_spn"
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
    notice_data.script_name = 'kh_gdpp_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'KH'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'KHR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'KM'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4

#Goods
#Note:Open the site and click on "សេចក្តីជូនដំណឹងការដេញថ្លៃ" and select "លទ្ធកម្មទំនិញ" than grab the data
#Ref_url=http://gdpp.gov.kh/bidding-announcement/goods-procurement

    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.item-content > p > a > font').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ថ្ងៃខែឆ្នាំចាប់ផ្តើមទទួលពាក្យ ៖
    # Onsite Comment -Note:Splite after "ថ្ងៃខែឆ្នាំចាប់ផ្តើមទទួលពាក្យ ៖" this .Take a first data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.item-content > ul > li:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -ថ្ងៃខែឆ្នាំឈប់ទទួលពាក្យ ៖
    # Onsite Comment -Note:Splite after "ថ្ងៃខែឆ្នាំឈប់ទទួលពាក្យ ៖" this .take a first data

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.item-content > ul > li:nth-child(3) > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_contract_type = 'ទំនិញ'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.contract_type_actual= 'ទំនិញ'    
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.item-content > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-12.col-lg-8 > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-12.col-lg-8 > div > div'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'GENERAL DEPARTMENT OF PUBLIC PROCUREMENT, MINISTRY OF ECONOMY AND FINANCE'
            customer_details_data.org_parent_id = '7717765'
            customer_details_data.org_country = 'KH'
            customer_details_data.org_language = 'KN'
        # Onsite Field -ទីតាំងភូមិសាស្ត្រអនុវត្តគម្រោង
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"ទីតាំងភូមិសាស្ត្រអនុវត្តគម្រោង")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Note:Click on "div.item-content > div > div.download > a" this ang grab the data

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.single-blog-post > div > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'div.file-caption-info').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, 'div.file-caption-info').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, 'div.file-actions > div > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass


#Works
#Note:Open the site and click on "សេចក្តីជូនដំណឹងការដេញថ្លៃ" and select "លទ្ធកម្មសំណង់" than grab the data
#Ref_url=http://gdpp.gov.kh/bidding-announcement/works-procurement

    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.item-content > p > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ថ្ងៃខែឆ្នាំចាប់ផ្តើមទទួលពាក្យ ៖
    # Onsite Comment -Note:Splite after "ថ្ងៃខែឆ្នាំចាប់ផ្តើមទទួលពាក្យ ៖" this .Take a first data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.item-content > ul > li:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -ថ្ងៃខែឆ្នាំឈប់ទទួលពាក្យ ៖
    # Onsite Comment -Note:Splite after "ថ្ងៃខែឆ្នាំឈប់ទទួលពាក្យ ៖" this .take a first data

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.item-content > ul > li:nth-child(3) > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Repleace following keywords with given keywords("សំណង់=Works")
    notice_data.notice_contract_type = 'សំណង់'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.contract_type_actual= 'សំណង់'     
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.item-content > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-12.col-lg-8 > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-12.col-lg-8 > div > div'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'GENERAL DEPARTMENT OF PUBLIC PROCUREMENT, MINISTRY OF ECONOMY AND FINANCE'
            customer_details_data.org_parent_id = '7717765'
            customer_details_data.org_country = 'KH'
            customer_details_data.org_language = 'KN'
        # Onsite Field -ទីតាំងភូមិសាស្ត្រអនុវត្តគម្រោង
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"ទីតាំងភូមិសាស្ត្រអនុវត្តគម្រោង")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Note:Click on "div.item-content > div > div.download > a" this ang grab the data

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.single-blog-post > div > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'div.file-caption-info').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, 'div.file-caption-info').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, 'div.file-actions > div > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass  

#Services
#Note:Open the site and click on "សេចក្តីជូនដំណឹងការដេញថ្លៃ" and select "លទ្ធកម្មសេវាកម្ម" than grab the data
#Ref_url=http://gdpp.gov.kh/bidding-announcement/services-procurement

#Note:Prajent time consulting data is nat available than take hold


    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.item-content > p > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -ថ្ងៃខែឆ្នាំចាប់ផ្តើមទទួលពាក្យ ៖
    # Onsite Comment -Note:Splite after "ថ្ងៃខែឆ្នាំចាប់ផ្តើមទទួលពាក្យ ៖" this .Take a first data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.item-content > ul > li:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -ថ្ងៃខែឆ្នាំឈប់ទទួលពាក្យ ៖
    # Onsite Comment -Note:Splite after "ថ្ងៃខែឆ្នាំឈប់ទទួលពាក្យ ៖" this .take a first data

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.item-content > ul > li:nth-child(3) > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_contract_type ='សេវាកម្ម'

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.contract_type_actual='សេវាកម្ម'    
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.item-content > p > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.col-12.col-lg-8 > div > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.col-12.col-lg-8 > div > div'):
            customer_details_data = customer_details()
            customer_details_data.org_name = 'GENERAL DEPARTMENT OF PUBLIC PROCUREMENT, MINISTRY OF ECONOMY AND FINANCE'
            customer_details_data.org_parent_id = '7717765'
            customer_details_data.org_country = 'KH'
            customer_details_data.org_language = 'KN'
        # Onsite Field -ទីតាំងភូមិសាស្ត្រអនុវត្តគម្រោង
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"ទីតាំងភូមិសាស្ត្រអនុវត្តគម្រោង")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -Note:Click on "div.item-content > div > div.download > a" this ang grab the data

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'div.single-blog-post > div > div'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_main.find_element(By.CSS_SELECTOR, 'div.file-caption-info').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, 'div.file-caption-info').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, 'div.file-actions > div > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass            
        
          
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["http://gdpp.gov.kh/bidding-announcement/goods-procurement","http://gdpp.gov.kh/bidding-announcement/works-procurement","http://gdpp.gov.kh/bidding-announcement/services-procurement"]
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,3):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div/div/div[1]/div/div[2]/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div/div/div[1]/div/div[2]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div/div/div[1]/div/div[2]/div/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[3]/div/div/div[1]/div/div[2]/div/div'),page_check))
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