from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "np_bolpatragov_ca"
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
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "np_bolpatragov_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'np_bolpatragov_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NP'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'NPR'
    notice_data.main_language = 'EN'
    notice_data.notice_type = 7
    notice_data.document_type_description = 'Contract Records Result'
    notice_data.notice_url = url
    
    # Onsite Field -Procurement Method
    # Onsite Comment -Note:If procurement_method is "NCB" than take 0 OR procurement_method is "ICB" than take 1 OR procurement_method is "OTHERS" than take 2

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        if procurement_method=='NCB':
            notice_data.procurement_method = 0
        elif procurement_method=='ICB':
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Name
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Amount
    # Onsite Comment -None

    try:
        notice_data.est_amount = float(tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text)
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -Contract Amount
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = float(tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass    
    
    # Onsite Field -Action
    # Onsite Comment -None

  
    
    # Onsite Field -Procurement Category
    # Onsite Comment -Note:Replace following keywords with given keywords("Goods=Supply","Works=Works","Consultancy=Consultancy","Other Services=Service")

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if notice_contract_type == 'Goods':
            notice_data.notice_contract_type = 'Supply'
        elif notice_contract_type == 'Works':
            notice_data.notice_contract_type = 'Works'
        elif notice_contract_type == 'Consultancy':
            notice_data.notice_contract_type = 'Consultancy'
        elif notice_contract_type == 'Services':
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -Procurement Category
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass    
    
    try:              
        customer_details_data = customer_details()
    # Onsite Field -PE Name
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        
        customer_details_data.org_country = 'NP'
        customer_details_data.org_language = 'NE'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_url = WebDriverWait(tender_html_element, 40).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'td:nth-child(8) > a')))
        page_main.execute_script("arguments[0].click();",notice_url) 
        time.sleep(2)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    # Onsite Field -Contract ID
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"Contract ID")]//following::td[1]/input'))).get_attribute('value')
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Project Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Project Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Notice Published Date
    # Onsite Comment -None

    try:
        publish_date = page_main.find_element(By.XPATH, '''(//*[contains(text(),"Start Date")])[1]//following::td[1]/input[1]''').get_attribute('value')
        publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return    

    if notice_data.publish_date is None:
        return    
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#createContractRecordsForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -None

    
    
# Onsite Field -None
# Onsite Comment -None

    try:      
        lot_details_data = lot_details()
        # Onsite Field -Contract Name
        # Onsite Comment -None
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = page_main.find_element(By.XPATH, '(//*[contains(text(),"Contract Name")])[1]//following::td[1]/input').get_attribute('value')
        # Onsite Field -None
        # Onsite Comment -None
        try:
            contract_start_date = page_main.find_element(By.XPATH, '(//*[contains(text(),"Start Date")])[1]//following::td[1]/input').get_attribute('value')
            contract_start_date = re.findall('\d+-\d+-\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass
        
        try:
            contract_end_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Completion/End Date")]//following::td[1]/input').get_attribute('value')
            contract_end_date = re.findall('\d+-\d+-\d{4}',contract_end_date)[0] 
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass
        
        try:
            award_details_data = award_details()

            # Onsite Field -Contractor Name
            # Onsite Comment -None

            award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Contractor Name")]//following::td[1]/input').get_attribute('value')


            # Onsite Field -DLP Start Date
            # Onsite Comment -None
            try:
                award_date = page_main.find_element(By.XPATH, '//*[contains(text(),"DLP Start Date")]//following:: td[1]/input').get_attribute('value')
                award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
            except:
                pass
            # Onsite Field -Contractor Address
            # Onsite Comment -None
            try:
                award_details_data.address = page_main.find_element(By.XPATH, '//*[contains(text(),"Contractor Address")]//following::td[1]/input').get_attribute('value')
            except:
                pass
        # Onsite Field -Total Payment
        # Onsite Comment -None
            try:
                award_details_data.grossawardvaluelc = float(page_main.find_element(By.XPATH, '//*[contains(text(),"Total Payment")]//following::td[1]/input').get_attribute('value'))
            except:
                pass
            
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    page_main.execute_script("window.history.go(-1)")
    time.sleep(3)
    WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="projDetailsTab"]/tbody/tr')))

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://bolpatra.gov.np/egp/loadContractRecordsListPublic"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="projDetailsTab"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="projDetailsTab"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
