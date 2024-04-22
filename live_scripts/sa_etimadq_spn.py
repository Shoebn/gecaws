
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
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sa_etimadq_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'sa_etimadq_spn'    
    notice_data.notice_no = '22'    
    notice_data.main_language = 'AR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'SAR'   
    notice_data.procurement_method = 2   
    notice_data.notice_type = 6
    
    # Onsite Field -تاريخ النشر :
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-12.col-md-9.p-0 > div > div > div > div > div:nth-child(1) > span").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if (notice_data.publish_date) is not None and (notice_data.publish_date) < threshold:
        return
    
    # Onsite Field -آخر موعد لتقديم وثائق التأهيل
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div > div > div:nth-child(3) > span.ml-3").text
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -الرقم المرجعي لدعوة التأهيل
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-12.col-md-12.p-0 > div > div > div:nth-child(1) > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-12 > div > div > div > div > div:nth-child(3) > h3 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url  
    
    # Onsite Field -اسم دعوة التأهيل
    # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, "//*[contains(text(),' اسم دعوة التأهيل')]//following::div[1]").text
        notice_data.notice_title = GoogleTranslator(source='ar', target='en').translate(notice_data.local_title)
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -اسم دعوة التأهيل
    # Onsite Comment -None
  
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -تفاصيل دعوة التأهيل
    # Onsite Comment -None

    try:
        notice_data.document_type_description = page_details.find_element(By.CSS_SELECTOR, 'div.title > h2').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -الجهة الحكومية
    # Onsite Comment -None
        customer_details_data.org_country = 'SA'
        try:
            org_name = page_details.find_element(By.XPATH, "//*[contains(text(),' الجهة الحكومية')]//following::div[1]").text
            customer_details_data.org_name = GoogleTranslator(source='ar', target='en').translate(org_name)
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
            
    # Onsite Field -المناطق
    # Onsite Comment -None

        try:
            org_address = page_details.find_element(By.XPATH, '/html/body/div[9]/div/div/div[2]/div/div/div[4]/div[2]/ul/li[2]/div/div[2]').text
            customer_details_data.org_address = GoogleTranslator(source='ar', target='en').translate(org_address)
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -اسم لجنة الفحص , اسم اللجنة الفنية
    # Onsite Comment -add both the field in  org_description "The name of the examination committee(اسم لجنة الفحص) =//*[contains(text(),' اسم لجنة الفحص')]//following::div[1]" + "Technical committee name(اسم اللجنة الفنية) : //*[contains(text(),' اسم اللجنة الفنية')]//following::div[1]"

        try:
            org_description = page_details.find_element(By.XPATH, "//*[contains(text(),' اسم لجنة الفحص')]//following::div[1]").text
            org_description1 = page_details.find_element(By.XPATH, "//*[contains(text(),' اسم اللجنة الفنية')]//following::div[1]").text
            org_description1 = (org_description+' , '+org_description1)
            customer_details_data.org_description =  GoogleTranslator(source='ar', target='en').translate(org_description1)
        except Exception as e:
            logging.info("Exception in org_description: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
     # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.main.main-raised > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
        
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
page_details.maximize_window()
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://tenders.etimad.sa/Qualification/QualificationsForVisitor"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')                                          
        logging.info(url)

        try:
            for page_no in range(2,22):                                                              
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@class="col-12 col-md-12 mb-4"]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="col-12 col-md-12 mb-4"]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@class="col-12 col-md-12 mb-4"]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@class="col-12 col-md-12 mb-4"]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
