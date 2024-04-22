from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "th_airportthai_ca"
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
SCRIPT_NAME = "th_airportthai_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'th_airportthai_ca'

    notice_data.main_language = 'TH'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'TH'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'THB'
    notice_data.procurement_method= 2
    
    notice_data.notice_type=7
    
    
    # Onsite Field -take all notice url from "Contract details"
    # Onsite Comment -None
    notice_data.notice_url = url
    
    # Onsite Field -Display Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > span:nth-child(3)").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date).split(':')[1]
        try:
            notice_data.publish_date = datetime.strptime(publish_date,' %d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.publish_date = datetime.strptime(publish_date,' %d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return


    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(5)').text.split(':')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'span:nth-child(11)').text.split(':')[1].strip()
        if ',' in est_amount:
            est_amount = re.sub("[^\d\.\,]", "", est_amount)
            notice_data.est_amount = float(est_amount.replace(',',''))
        else:
            notice_data.est_amount=float(est_amount)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > strong').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -split data from "Type of document/ประเภทเอกสาร  " to "Year of procurement/ปีที่จัดซื้อจัดจ้าง
    # Onsite Comment -None

    try:
        document_type_description = tender_html_element.text.split('ประเภทเอกสาร : ')[1].split('\n')[0]
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')                     
    except:
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'AIRPORTS OF THAILAND PUBLIC CO LTD'
        customer_details_data.org_language = 'TH'
        customer_details_data.org_country = 'TH'
        customer_details_data.org_parent_id = '7548547'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
#   
        lot_details_data = lot_details()
        lot_details_data.lot_number=1
    # Onsite Field -None
    # Onsite Comment -None

        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            lot_details_data.lot_description =notice_data.notice_title
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            lot_details_data.lot_grossbudget = notice_data.grossbudgetlc 
        except Exception as e:
            logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
            pass

    # Onsite Field -split data from "Contract Start Date /วันเริ่มต้นสัญญา   " to "Contract end date, Contract termination date /วันที่สิ้นสุดสัญญา"
    # Onsite Comment -None

        try:
            contract_start_date = tender_html_element.text.split('วันเริ่มต้นสัญญา : ')[1].split('\n')[0]
            contract_start_date = GoogleTranslator(source='auto', target='en').translate(contract_start_date)
            if '.' in contract_start_date:
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
            else:
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

    # Onsite Field -split data from "Contract termination date /วันที่สิ้นสุดสัญญา   " to "Contract end date,Payment schedule /กำหนดเบิกจ่ายเงิน"
    # Onsite Comment -None

        try:
            contract_end_date = tender_html_element.text.split('วันที่สิ้นสุดสัญญา : ')[1].split('\n')[0]
            contract_end_date = GoogleTranslator(source='auto', target='en').translate(contract_end_date)
            if '.' in contract_end_date:
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
            else:
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass

    # Onsite Field -None
    # Onsite Comment -None

        try:
            award_details_data = award_details()
            bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > span:nth-child(9)').text
            award_details_data.bidder_name = GoogleTranslator(source='auto', target='en').translate(bidder_name).split(' : ')[1]
            award_details_data.grossawardvaluelc=notice_data.grossbudgetlc
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lots: {}".format(type(e).__name__)) 
        pass

    try:              
        attachments_data = attachments()
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.download_file').get_attribute('href')
        attachments_data.file_name = tender_html_element.find_element(By.CSS_SELECTOR, 'a.download_file').text
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ["https://aotdatainfo.airportthai.co.th/bidding/Category/index/140", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/142", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/144", "https://aotdatainfo.airportthai.co.th/bidding/Category/index/143"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container"]/div[4]/div[2]/div[2]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container"]/div[4]/div[2]/div[2]/div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container"]/div[4]/div[2]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="container"]/div[4]/div[2]/div[2]/div'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            pass
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
