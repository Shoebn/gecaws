from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_ac_ungm_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download
from selenium.webdriver.common.keys import Keys

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_ac_ungm_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()

    notice_data.script_name = 'ac_ungm_spn'
    notice_data.main_language = 'EN'
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2


    try:
        performance_country_data = performance_country()
        p_country = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(8)').text
        performance_country_data.performance_country = fn.procedure_mapping("assets/us_ungm_countrycode.csv",p_country)
        if performance_country_data.performance_country == None:
            performance_country_data.performance_country = 'US'
    except:
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'US'
     
    
    try:
        notice_data.source_of_funds = 'International agencies'
        f_agenciess = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableCell.resultAgency span').get_attribute('innerHTML')
        if 'UN Secretariat' in f_agenciess or 'IRENA' in f_agenciess:
            f_agenciess = 'UNDP'
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/us_ungm_funding.csv",f_agenciess)
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(6)').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
        if 'Request for EOI' in notice_data.document_type_description:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if len(notice_data.notice_title) < 5:
              notice_data.notice_title = notice_data.notice_no 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.tableRow > div:nth-child(4)").text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.tableRow > div:nth-child(3)").text
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(2) > div > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
time.sleep(40)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.ungm.org/Public/Notice'] 
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        start_date = th.strftime('%d-%b-%Y')
        page_main.find_element(By.XPATH,'//*[@id="txtNoticePublishedFrom"]').send_keys(start_date)
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="txtNoticeDeadlineFrom"]').clear()
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="lnkSearch"]').click()
        time.sleep(3)
        for scroll in  range(1,50):
            page_main.find_element(By.CSS_SELECTOR,'body').send_keys(Keys.END)
            time.sleep(5)
            
        page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tblNotices"]/div[2]/div'))).text
        rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblNotices"]/div[2]/div')))
        length = len(rows)
        for records in range(0,length):
            tender_html_element = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblNotices"]/div[2]/div')))[records]
            extract_and_save_notice(tender_html_element)
            if notice_count >= MAX_NOTICES:
                break

            if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break                                    

        logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
