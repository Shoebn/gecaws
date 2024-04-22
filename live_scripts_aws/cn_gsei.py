from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cn_gsei"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cn_gsei"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
      
    notice_data.main_language = 'ZH'
    
    notice_data.currency = 'CNY'
    
    notice_data.script_name = 'cn_gsei'
    
    notice_data.procurement_method = 2
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    

    try:
        notice_data.document_type_description = '公开招标 '  
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.pageList > ul > li> span").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.pageList > ul > li> a').text
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
        notice_data.local_description = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.pageList > ul > li >a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except:
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div.article').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
 
    try:              
        customer_details_data = customer_details()
        pg_data = page_details.find_element(By.CSS_SELECTOR, 'div > div.article').text

        try:
            if '招标人：' in pg_data:
                org_name = pg_data.split('招标人：')[1].split('\n')[0] 
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            elif '招 标 人：' in pg_data:
                org_name = pg_data.split('招 标 人：')[1].split('\n')[0] 
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            elif '九、招标代理机构：' in pg_data:
                org_name = pg_data.split('九、招标代理机构：')[1].split('\n')[0]  
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            elif '采 购 人：' in pg_data:
                org_name = pg_data.split('采 购 人：')[1].split('\n')[0] 
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            elif '招标单位：' in pg_data:
                org_name = pg_data.split('招标单位：')[1].split('\n')[0] 
                customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            else:
                customer_details_data.org_name = "Gansu Economic Research Institute"
        except:
            customer_details_data.org_name = "Gansu Economic Research Institute"
        customer_details_data.org_country = 'CN'

        try:
            if '联系人：'in pg_data:
                contact_person = pg_data.split('联系人：')[1].split('\n')[0] 
                customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
            elif '联 系 人：' in pg_data:
                contact_person = pg_data.split('联 系 人：')[1].split('\n')[0] 
                customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
            elif '联 系 人：' in pg_data:
                contact_person = pg_data.split('联 系 人：')[1].split('\n')[0]  
                customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
            elif '项目联系人：' in pg_data:
                contact_person = pg_data.split('项目联系人：')[1].split('\n')[0]    
                customer_details_data.contact_person = GoogleTranslator(source='auto', target='en').translate(contact_person)
            else:
                pass

        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass


        try:
            if '联系电话：' in pg_data:
                customer_details_data.org_phone = pg_data.split('联系电话：')[1].split('\n')[0] 
            elif '电    话：' in pg_data:
                customer_details_data.org_phone = pg_data.split('电    话：')[1].split('\n')[0]             
            elif '行号：' in pg_data:
                customer_details_data.org_phone = pg_data.split('行号：')[1].split('\n')[0]             
            elif '办公电话： ' in pg_data:
                customer_details_data.org_phone = pg_data.split('办公电话： ')[1].split('\n')[0]             
            elif '办公电话：' in pg_data:
                customer_details_data.org_phone = pg_data.split('办公电话：')[1].split('\n')[0]             
            elif '电 话：' in pg_data:
                customer_details_data.org_phone = pg_data.split('电 话：')[1].split('\n')[0]             
            elif '电话：' in pg_data:
                customer_details_data.org_phone = pg_data.split('电话：')[1].split('\n')[0]             
            else:
                pass

        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) 
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
    urls = ['https://www.gsei.com.cn/html/1336/'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div > div.pageList > ul > li:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div > div.pageList > ul > li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div > div.pageList > ul > li')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div > div.pageList > ul > li:nth-child(1)'),page_check))
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
