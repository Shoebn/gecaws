from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_beeindia"
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
SCRIPT_NAME = "in_beeindia"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_beeindia'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    notice_data.notice_url = url
    
    # Onsite Field -Tender Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-title').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publish Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.views-field.views-field-publish-on").text
        publish_date = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td.views-field.views-field-unpublish-on").text
        try:
            notice_deadline = re.findall('\d+-\d+-\d{4} \d+:\d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        except:    
            notice_deadline = re.findall('\d+/\d+/\d{4} - \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Bureau of Energy Efficiency'
        customer_details_data.org_parent_id = '7305558'
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_address = '4th Floor, Sewa Bhawan, R. K. Puram, New Delhi - 110066 (INDIA)'
        customer_details_data.org_phone = '011-26766700'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        attachments_data = attachments()
        # Onsite Field -Corrigendum
        # Onsite Comment -1.don't take file_extension in file_name.

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-2 > div > div > div > div > div > div > div.doc-name.pdf-icon > span').text.split(".")[0].strip()
        
        # Onsite Field -Corrigendum >> Format:
        # Onsite Comment -None

        try:
            attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-2 > div > div > div > div > div > div > div.doc-types > div.filesizelang.format > span').text
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Corrigendum >> Size:
        # Onsite Comment -None

        try:
            attachments_data.file_size = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-2 > div > div > div > div > div > div > div.doc-types > div.filesizelang.size > span').text
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Corrigendum
        # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-2 > div > div > div > div > div > div > div.doc-name.pdf-icon > span > a').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass   
    
    try:              
        attachments_data = attachments()
        # Onsite Field -NIT
        # Onsite Comment -1.don't take file_extension in file_name.

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-1 > div > div > div > div > div > div > div.doc-name.pdf-icon > span').text.split(".")[0].strip()
        
        # Onsite Field -NIT >> Format:
        # Onsite Comment -None

        try:
            attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-1 > div > div > div > div > div > div > div.doc-types > div.filesizelang.format > span').text
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        # Onsite Field -NIT >> Size:
        # Onsite Comment -None

        try:
            attachments_data.file_size = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-1 > div > div > div > div > div > div > div.doc-types > div.filesizelang.size > span > font > font').text
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -NIT
        # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view-1 > div > div > div > div > div > div > div.doc-name.pdf-icon > span > a').get_attribute('href')

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        # Onsite Field -Corrigendum
        # Onsite Comment -1.don't take file_extension in file_name.

        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view > div > div > div > div > div.doc-name.pdf-icon > span').text.split(".")[0].strip()
       
        # Onsite Field -Corrigendum >> Format:
        # Onsite Comment -None

        try:
            attachments_data.file_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view > div > div > div > div > div.doc-types > div.filesizelang.format > span').text
        except Exception as e:
            logging.info("Exception in file_type: {}".format(type(e).__name__))
            pass

        # Onsite Field -Corrigendum >> Size:
        # Onsite Comment -None

        try:
            attachments_data.file_size = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view > div > div > div > div > div.doc-types > div.filesizelang.size > span').text
        except Exception as e:
            logging.info("Exception in file_size: {}".format(type(e).__name__))
            pass

        # Onsite Field -Corrigendum
        # Onsite Comment -None

        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.views-field.views-field-view > div > div > div > div > div.doc-name.pdf-icon > span > a').get_attribute('href')
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass            
        

    notice_data.notice_text = tender_html_element.get_attribute("outerHTML")
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://beeindia.gov.in/en/tenders"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-custom-content"]/div/div/div/div[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="block-custom-content"]/div/div/div/div[2]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
