from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "za_etenders_spn"
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
tnotice_count = 0
SCRIPT_NAME = "za_etenders_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"


def extract_and_save_notice(tender_html_element,records):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()

    notice_data.script_name = 'za_etenders_spn'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ZA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'ZAR'
    notice_data.procurement_method = 2
    notice_data.notice_type = 4

    # Onsite Field -Tender Description
    # Onsite Comment -split the data from tender_html_page

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "td.break-word").text
        cpv_codes = fn.CPV_mapping("assets/za_etenders_category.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass

    # Onsite Field -Advertised
    # Onsite Comment -split the data from tender_html_page

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_url = 'https://www.etenders.gov.za/Home/opportunities?id=1'
    try:
        notice_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)')
        notice_click.click()
    except:
        pass
    time.sleep(2)
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'tbody  table > tbody').get_attribute("outerHTML")
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Tender Number:
    # Onsite Comment -split the data from page_main

    try:
        notice_data.notice_no = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Number")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tender Type:
    # Onsite Comment -split the data from page_main

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Tender Type:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Closing Date:
    # Onsite Comment -split the data from page_main

    try:
        notice_deadline = page_main.find_element(By.XPATH, "//*[contains(text(),'Closing Date:')]//following::td[1]").text
        notice_deadline = re.findall('\d+ \w+ \d{4} - \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

# Onsite Field -None
# Onsite Comment -None

    try:
        customer_details_data = customer_details()
    # Onsite Field -Department:
    # Onsite Comment -split the data from page_main

        customer_details_data.org_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Department:")]//following::td[1]').text

    # Onsite Field -Province:
    # Onsite Comment -split the data from page_main

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Province:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Place where goods, works or services are required:
    # Onsite Comment -split the data from page_main

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Place where goods, works or services are required:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Contact Person:
    # Onsite Comment -split the data from page_main

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Contact Person:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Email:
    # Onsite Comment -split the data from page_main

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Telephone number:
    # Onsite Comment -split the data from page_main

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telephone number:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -FAX Number:
    # Onsite Comment -split the data from page_main

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"FAX Number:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'ZA'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__))
        pass

# Onsite Field -TENDER DOCUMENTS
# Onsite Comment -split the data from page_main

    try:
        for single_record in page_main.find_elements(By.XPATH, '//b[contains(text(),"TENDER DOCUMENTS")]//following-sibling::a'):
            file_name = single_record.text
            if file_name !='':
                attachments_data = attachments()
                # Onsite Field -TENDER DOCUMENTS
                # Onsite Comment -split only file_name for ex. "SUPPLY AND DELIVERY BUILDING MATERIAL ( PLUMBING & CARPENTRY) FOR THREE YEARS.pdf" , here split only "SUPPLY AND DELIVERY BUILDING MATERIAL ( PLUMBING & CARPENTRY) FOR THREE YEARS"

                attachments_data.file_name = file_name
            # Onsite Field -TENDER DOCUMENTS
            # Onsite Comment -split only file_type for ex. "SUPPLY AND DELIVERY BUILDING MATERIAL ( PLUMBING & CARPENTRY) FOR THREE YEARS.pdf" , here split only "pdf"

                try:
                    attachments_data.file_type = single_record.text.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

            # Onsite Field -TENDER DOCUMENTS
            # Onsite Comment -None

                attachments_data.external_url = single_record.get_attribute('href')
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__))
        pass
    try:
        colse_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)')
        colse_click.click()
        time.sleep(2)
    except:
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')


# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.etenders.gov.za/Home/opportunities?id=1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):#50
            try:
                WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[@id="btnActive"]')))
                time.sleep(2)
                page_main.execute_script("window.scrollTo(0, 200);")
                time.sleep(2)
            except:
                pass
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tendeList"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tendeList"]/tbody/tr')))
            length = len((rows))
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tendeList"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element,records)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
            
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0
            
            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tendeList"]/tbody/tr'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
