from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "vn_muasamcongopp_pp"
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
from selenium.webdriver.support.ui import Select

##---------------------------------------------------------------------********************************************************************-----------------------------------------------------

#     NOTE- after clicking on "Tìm kiếm nâng cao", "div.content__search__body > a >>>>>>>> select "Thời gian đăng tải" and "Thời điểm đóng thầu" dates                                                       
#     NOTE- " select "Tìm theo :" >>>    >>>      Kế hoạch tổng thể lựa chọn nhà thầu    -- as notice_type "3" >>>"Tìm kiếm"..... if tender page redirects to the main page click on ,"Search"
#     NOTE- use vpn to load the website 
##---------------------------------------------------------------------********************************************************************-----------------------------------------------------  
NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "vn_muasamcongopp_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'vn_muasamcong_pp'
    
    notice_data.main_language = 'VI'
    
    notice_data.currency = 'VND'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'VI'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 3
    
    notice_data.document_type_description = 'Kế hoạch tổng thể lựa chọn nhà thầu'
    
    notice_data.procurement_method = 2
    

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-10.content__body__left__item__infor__contract  h5').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ngày đăng tải / Publication date
    #  01/02/2024 - 11:07
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-8.content__body__left__item__infor__contract__other > h6:nth-child(2) > span").text
        publish_date = re.findall('\d+/\d+/\d{4} - \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Mã kế hoạch tổng thể LCNT /
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.justify-content-between.align-items-center  p').text.split("Mã kế hoạch tổng thể LCNT : ")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
   
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-10.content__body__left__item__infor__contract > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -if present take data  from following tabs "Hồ sơ mời thầu",  "Làm rõ HSMT",  "Hội nghị tiền đấu thầu",  "Kiến nghị" 
    # Onsite Comment -# Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*[@id="bid-closed"]/div"
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.d-flex > div.tab-content').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Thời gian thực hiện dự án
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '''//*[contains(text(),'Thời gian thực hiện ')]//following::div[1]''').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tổng mức đầu tư
    try:
        est_amount = page_details.find_element(By.XPATH, '''//*[contains(text(),'Tổng mức đầu tư')]//following::div[1]''').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
        notice_data.netbudgetlc = notice_data.est_amount 
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Employer / Chủ đầu tư

        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-8.content__body__left__item__infor__contract__other > h6:nth-child(1) > span').text
        if "Chủ đầu tư :" in org_name:
            customer_details_data.org_name = org_name.split("Chủ đầu tư :")[1].strip()
        else:
            customer_details_data.org_name = org_name

        customer_details_data.org_country = 'VN'
        customer_details_data.org_language = 'VI'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_vpn(arguments) 
page_details = fn.init_chrome_driver_vpn(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://muasamcong.mpi.gov.vn/vi/web/guest"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        close_popup = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#popup-close')))
        page_main.execute_script("arguments[0].click();",close_popup)
        time.sleep(2)
        
        Tìm_kiếm_nâng_ca_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.content__wrapper__header > div.content__search__body > a > button')))
        page_main.execute_script("arguments[0].click();",Tìm_kiếm_nâng_ca_click)
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-advantage-haunt"]/div/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div/div')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        click = page_main.find_elements(By.CSS_SELECTOR, "div.ant-select-dropdown-content > ul > li")[2]
        click.click()
        time.sleep(5)
            
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search-advantage-haunt > div > div > div > div > div > div.content__footer > button:nth-child(2)')))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        for page_no in range(1,25):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="bid-closed"]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bid-closed"]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                if notice_count == 10:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search-home"]/div/div[3]/div[1]/div[4]/div/div/button[2]/i')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="bid-closed"]/div'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
