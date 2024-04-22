from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cross_check_gb_findtenserv_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cross_check_gb_findtenserv_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "cross_check_output"


def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = cross_check_output()
    notice_data.script_name = 'gb_findtenserv_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'

    notice_data.currency = 'GBP'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
        
    notice_data.class_at_source = 'CPV'

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > dd').text.split(':')[1]
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass  
        
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR,'div.search-result-header > h2').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > dd").text
        try:
            notice_deadline = re.findall('\d+ \w+ \d{4}, \d+:\d+[apAP][mM]', notice_deadline )[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline ,'%d %B %Y, %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_deadline = re.findall('\d+ \w+ \d{4}', notice_deadline )[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline ,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')

        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
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
    urls = ['https://www.find-tender.service.gov.uk/Search/Results']
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            click_1 = page_main.find_element(By.XPATH, "//input[contains(@name,'stage[4]')]").click()
            time.sleep(3)
        except:
            pass
        try:
            click_2 = page_main.find_element(By.XPATH, "//input[contains(@name,'stage[3]')]").click()
            time.sleep(3)
        except:
            pass
        try:
             click_2 = page_main.find_element(By.XPATH, "//input[contains(@name,'stage[1]')]").click()
        except:
            pass
        try:
            click_3 = page_main.find_element(By.XPATH, "//button[contains(@class,'govuk-button form-control')]").click()
            time.sleep(3)
        except:
            pass

        for page_no in range(1,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div[1]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))
            length = len(rows)

            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.standard-paginate-next.govuk-link.break-word')))
                page_main.execute_script("arguments[0].click();", next_page)
                logging.info("Next page")
                time.sleep(5)
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH, '//*[@id="listTemplate"]/table/tbody/tr'), page_check))
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
