from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bd_cptu_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bd_cptu_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'bd_cptu_ca'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BD'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BDT'
    
    notice_data.notice_type = 7

#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []

    
    # Onsite Field -Ref No., Title & Advertisement Date
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date of Notification of Award
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Ministry & Agency
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.ID, '#bodyContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Contract Award for
    # Onsite Comment -1.replace folloeing keyword with given keyword("Goods=Supply","Works=Works","Services=Service")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award for")]//following::td[1]').text
        if "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
        elif "Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Invitation/Proposal Reference No
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation/Proposal Reference No")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.in the given field written as "NCT" then take "procurement_method=0","ICT" then take "procurement_method=1" otherwise take "procurement_method=2"

    try:
        procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Method")]//following::td[1]').text
        if "NCT" in procurement_method:
            notice_data.procurement_method = 0
        elif "ICT" in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Budget and Source of Funds
    # Onsite Comment -None

    try:
        notice_data.source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Budget and Source of Funds")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender/Proposal Package No
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender/Proposal Package No")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender/Proposal Package No
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Proposed Date of Contract Completion")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description of Contract")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Brief Description of Contract
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description of Contract")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
 
    try:              
    # Onsite Field -Development Partner
    # Onsite Comment -None

        funding_agency1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Development Partner")]//following::td[1]').text
        funding_agency2 =['',"International Development Association (IDA)" ,"IDA", "None"]
        if funding_agency1 not in funding_agency2:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = fn.procedure_mapping("assets/bd_cptu_ca_fundingagencycode.csv",funding_agency1)
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'BD'
        # Onsite Field -Procuring Entity & Procurement Method
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        
        # Onsite Field -Ministry & Agency
        # Onsite Comment -None

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -District
        # Onsite Comment -None

        try:
            customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Procuring Entity Code
        # Onsite Comment -None

        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Entity Code")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Name of Authorised Officer
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Authorised Officer")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1

        # Onsite Field -Ref No., Title & Advertisement Date
        # Onsite Comment -None

        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        lot_details_data.lot_title_english=lot_details_data.lot_title
    # Onsite Field -Contract Award for
    # Onsite Comment -1.replace folloeing keyword with given keyword("Goods=Supply","Works=Works","Services=Service")

        try:
            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award for")]//following::td[1]').text
            if "Goods" in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = "Supply"
            elif "Works" in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = "Works"
            elif "Services" in lot_details_data.lot_contract_type_actual:
                lot_details_data.contract_type = "Service"
            else:
                pass
        except Exception as e:
            logging.info("Exception in contract_type: {}".format(type(e).__name__))
            pass

        try:
            award_details_data = award_details()

                # Onsite Field -Contract Awarded to
                # Onsite Comment -None

            award_details_data.bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text

                # Onsite Field -Contract Awarded to
                # Onsite Comment -None
            try:
                award_details_data.address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in address: {}".format(type(e).__name__))
                pass
            # Onsite Field -Contract Value
            # Onsite Comment -None
            try:
                grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
                if " " in grossawardvaluelc:
                    grossawardvaluelc1 =grossawardvaluelc.split(" ")[1].strip()
                    grossawardvaluelc1 = re.sub("[^\d\.\,]","",grossawardvaluelc1)
                    award_details_data.grossawardvaluelc=float(grossawardvaluelc1.replace(',','').strip())
                else:
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc=float(grossawardvaluelc.replace(',','').strip())
            except Exception as e:
                logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                pass
                # Onsite Field -Date of Contract Signing
                # Onsite Comment -None
            try:
                award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Contract Signing")]//following::td[1]').text
                award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
            except Exception as e:
                logging.info("Exception in award_date: {}".format(type(e).__name__))
                pass
            award_details_data.award_details_cleanup()
            lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        if award_details_data.bidder_name != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
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
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://cptu.gov.bd/contract-award/contract-award-list.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/section[2]/section/div/div/div[2]/div/form/div[7]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/section/div/div/div[2]/div/form/div[7]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/section/div/div/div[2]/div/form/div[7]/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
