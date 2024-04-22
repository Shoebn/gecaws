from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_it_lombardia_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_it_lombardia_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "cross_check_output"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    notice_data.script_name = 'it_lombardia_spn'
    notice_data.main_language = 'IT'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IT'
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.additional_source_name = 'ARIA'

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        codice_gara = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if codice_gara=='.':
            codice_gara = codice_gara.replace('.','')
        else:
            codice_gara =codice_gara
    except:
        pass
    
    try:
        if codice_gara!='':
            local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            notice_data.local_title = local_title.replace(codice_gara,'').replace('-','').replace('_','').replace('-','').strip()
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        else:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a').get_attribute("href")
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('=')[1].strip()
        except:
            try:
                notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in notice_no: {}".format(type(e).__name__))
                pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        publish_date = re.findall('\d+/\d+/\d{4}', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(11)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+', notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/it_lombardia_spn_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount_data = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount_data)
        notice_data.est_amount = est_amount.replace('.','').replace(',','.').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        if "€" in est_amount_data:
            notice_data.netbudgetlc = notice_data.est_amount
            notice_data.netbudgeteuro= notice_data.est_amount
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
        
    try:
        customer_details_data = customer_details()
        customer_details_data.org_country = 'IT'
        customer_details_data.org_language = 'IT'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments = ['--incognito', 'ignore-certificate-errors', 'allow-insecure-localhost', '--start-maximized']

page_main = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.sintel.regione.lombardia.it/eprocdata/sintelSearch.xhtml']
    url_retry = 1
    for url in urls:
        fn.load_page(page_main, url, 10)
        logging.info('----------------------------------')
        logging.info(url)
        
        time.sleep(2)
        page_main.find_element(By.XPATH, '//div[@id="auctionStateArrow"]').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[1]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[2]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[4]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[8]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[9]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[10]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[12]/label/input').click()
        time.sleep(1)
        page_main.find_element(By.XPATH, '//ul[@id="auctionStatus"]//li[14]/label/input').click()
        time.sleep(2)
        try:
            page_main.find_element(By.XPATH, '//input[@value="Applica"]').click()
        except:
            page_main.find_element(By.XPATH, '//input[@value="Applica"]').click()
        time.sleep(5)
        
        for page_no in range(2,50):#50
            page_check = WebDriverWait(page_main,180).until(EC.presence_of_element_located((By.XPATH, '//*[@id="result"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                time.sleep(2)
                tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="result"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break   
                    
                if notice_count == 50:
                    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0

            try:
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT, str(page_no))))
                page_main.execute_script("arguments[0].click();", next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="result"]/tbody/tr'), page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:" + str(e))
finally:
    page_main.quit()
    output_json_file.copycrosscheckoutputJSONToServer(output_json_folder)
