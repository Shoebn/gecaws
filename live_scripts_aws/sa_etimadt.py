from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "sa_etimadt"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 20000
notice_count = 0
SCRIPT_NAME = "sa_etimadt"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'sa_etimadt'
    
    notice_data.main_language = 'AR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'SAR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
  
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > h3').text
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
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-12.border-bottom > div > div:nth-child(1)").text.split('تاريخ النشر :')[1]
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) > span:nth-child(2)").text
        notice_deadline = GoogleTranslator(source='auto', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > span:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-12.pt-2 > span').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        document_cost = tender_html_element.find_element(By.CSS_SELECTOR, '  div.tender-coast > div').text
        document_cost = re.sub("[^\d+]",'',document_cost)
        notice_data.document_cost = float(document_cost)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-6.text-left').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/sa_etimad_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-12 > p >  a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except:
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#d-1 > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        notice_data.notice_text += tender_html_element.get_attribute("outerHTML")
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, 'li:nth-child(7) > div > div.col-8.etd-item-info > span').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, "//*[contains(text(),' نوع المنافسة')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'SA'

        try:
            org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-12.border-bottom > div > div:nth-child(4) > p').text
            customer_details_data.org_name = GoogleTranslator(source='auto', target='en').translate(org_name)
            customer_details_data.org_name =customer_details_data.org_name.split('the details')[0]
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)

    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(options=options)
time.sleep(20)


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://tenders.etimad.sa/Tender/AllTendersForVisitor'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,22):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="cardsresult"]/div[1]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="cardsresult"]/div[1]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="cardsresult"]/div[1]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="cardsresult"]/div[1]/div'),page_check))
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

