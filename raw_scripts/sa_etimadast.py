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
from webdriver_manager.chrome import ChromeDriverManager
import gec_common.OutputJSON
import functions as fn
from functions import ET
import gec_common.Doc_Download
from hijri_converter import Hijri

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sa_etimadast"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'sa_etimadast'
    
    notice_data.main_language = 'AR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SA'
    notice_data.performance_country.append(performance_country_data)
        
    notice_data.currency = 'SAR'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note: use vpn code for this script : United States VPN
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > h5').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_summary_english)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"الرقم المرجعي للقائمة "  = List reference number
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li:nth-child(2) > div > div.col-8.etd-item-info > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"نوع المنافسة " = competition type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-body > div > ul > li:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -"تاريخ النشر " =  date of publication
    # Onsite Comment -None

    try:
        pub_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.card-body > div > ul > li:nth-child(8)").text
        publication_date = re.findall('\d{4}-\d+-\d+',pub_date)[0]
        year = publication_date.split('-')[0]
        month = publication_date.split('-')[1]
        date = publication_date.split('-')[-1]
        hijri_converter = Hijri(int(year), int(month), int(date)).to_gregorian()
        notice_data.publish_date = datetime.strptime(str(hijri_converter),'%Y-%m-%d').strftime('%Y/%m/%d')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -"اخر موعد لاستقبال طلبات الانضمام للقائمة " = Deadline for receiving applications to join the list
    # Onsite Comment -None

    try:
        notice_end_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.card-body > div > ul > li:nth-child(7)").text
        end_date = re.findall('\d{4}-\d+-\d+',notice_end_date)[0]
        year = end_date.split('-')[0]
        month = end_date.split('-')[1]
        date = end_date.split('-')[-1]
        hijri_converter = Hijri(int(year), int(month), int(date)).to_gregorian()
        notice_data.notice_deadline = datetime.strptime(str(hijri_converter),'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
  
    # Onsite Field -" التفاصيل " =  THE DETAILS
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.card-footer.row > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    logging.info(notice_data.notice_url)
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#basicStepDiv').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH,"//*[contains(text(),'تعريف القائمة')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -" الشروط الازمة للانضمام للقائمة " = Crisis conditions for joining the list
    # Onsite Comment -None

    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, "//*[contains(text(),' الشروط الازمة للانضمام للقائمة')]//following::div[1]").text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()
    # Onsite Field -" الجهة الحكومية " = The government agency
    # Onsite Comment -None
        customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),' الجهة الحكومية')]//following::div[1]/span[1]").text
        customer_details_data.org_country = 'SA'
    # Onsite Field -"العنوان" = the address
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'العنوان')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_main_activity = tender_html_element.find_element(By.CSS_SELECTOR, " li:nth-child(6) > div > div.col-8.etd-item-info > span").text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -"الهاتف" = the phone
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'الهاتف')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -"فاكس" =  fax
    # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, "//*[contains(text(),'فاكس')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -"البريد الإلكتروني" = E-mail
    # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'البريد الإلكتروني')]//following::div[1]").text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(executable_path=ChromeDriverManager().install(),options=options)
time.sleep(20)

options = webdriver.ChromeOptions()
options.add_extension("Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_details = webdriver.Chrome(executable_path=ChromeDriverManager().install(),options=options)
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://tenders.etimad.sa/AnnouncementSuppliersTemplate/AllSupplierAnnouncementSupplierTemplates'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,25):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[9]/div/div/form/div/div[2]/div[2]/div[1]/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[9]/div/div/form/div/div[2]/div[2]/div[1]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[9]/div/div/form/div/div[2]/div[2]/div[1]/div/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[9]/div/div/form/div/div[2]/div[2]/div[1]/div[1]/div'),page_check))
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
