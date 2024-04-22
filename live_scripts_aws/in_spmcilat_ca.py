from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "in_spmcilat_ca"
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
SCRIPT_NAME = "in_spmcilat_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'in_spmcilat_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'EN'
    
    notice_data.currency = 'INR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7


#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []
    
    # Onsite Field -Tender No
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-tender_no.dtr-control').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-subject').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date Of Publication
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.col-date_of_publication").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-button > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#primary > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, '#primary > main').text.split("Item/Nature of work : ")[1].split("Mode of Tender Enquiry : ")[0].split("Mode of Tender Enquiry :")[0].strip()
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -Contract No :
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract No")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'Security Printing and Minting Corporation of India'
        customer_details_data.org_parent_id = '7053515'
        customer_details_data.org_country = 'IN'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Unit Name
        # Onsite Comment -None

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-unit_name').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Subject
        # Onsite Comment -None

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title
    
        # Onsite Field -Actual Date of Start of Work :
        # Onsite Comment -1.split between "Actual Date of Start of Work :" and "Award Date :".

        try:
            contract_start_date = page_details.find_element(By.CSS_SELECTOR, '#primary > main').text.split("Actual Date of Start of Work :")[1].split("Actual Date of Completion :")[0].split("Award Date :")[0].strip()
            contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Actual Date of Completion
        # Onsite Comment -1.split between "Actual Date of Completion :" and "Award Upload Date :".

        try:
            contract_end_date = page_details.find_element(By.CSS_SELECTOR, '#primary > main').text.split("Actual Date of Completion :")[1].split("Award Date :")[0].split("Award Upload Date :")[0].strip()
            contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
            pass
        
        award_details_data = award_details()

        try:
            # Onsite Field -Award Date
        # Onsite Comment -None
            award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td.col-award_date').text
            award_date = re.findall('\d{4}-\d+-\d+',award_date)[0]
            award_details_data.award_date = datetime.strptime(award_date,'%Y-%m-%d').strftime('%Y/%m/%d')
        except:
            pass
        # Onsite Field -Name of Contractor :
        # Onsite Comment -None

        award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Contractor")]//following::p[1]').text
        # Onsite Field -Value of Contract :
        # Onsite Comment -None
        try:
            grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Value of Contract")]//following::p[1]').text
            grossawardvaluelc = re.sub("[^\d\,]", "", grossawardvaluelc)
            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','').strip())
        except:
            pass
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.spmcil.com/en/awarded-tenders/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div[2]/div/div/main/article/div/div/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/main/article/div/div/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/main/article/div/div/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ptp_a4462f8403b67833_1_next")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[1]/div[2]/div/div/main/article/div/div/div/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
