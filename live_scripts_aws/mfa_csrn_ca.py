#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_csrn_ca"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_csrn_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'mfa_csrn_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'USD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Country
    # Onsite Comment -1.csv file is pulled name as "mfa_csrn_ca_countrycode.csv"	2."Hong Kong, China=CN" and "Regional=PH"

    try:
        performance_country_data = performance_country()
        performance = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(1)').text

        if 'Regional' in performance:
            performance_country_data.performance_country = 'PH'

        elif 'China' in  performance or 'Hong Kong' in performance:

            performance_country_data.performance_country = 'CN'
        else:
            performance_country_data.performance_country = fn.procedure_mapping("assets/mfa_csrn_ca_countrycode.csv",performance)
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    # Onsite Field -Project Name
    # Onsite Comment -None
    
    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = '106'
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(2)').text.split('(')[-1].split(')')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    try:
        org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(1)').text
        if 'Regional' in org_country:
            org_country  = 'PH'
        elif 'China' in  org_country or 'Hong Kong' in org_country:
            org_country = 'CN'
        else:
            org_country = fn.procedure_mapping("assets/mfa_csrn_ca_countrycode.csv", org_country )
    except:
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(3)').text
    bidder_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1s:nth-child(4)').text
    
    try:
        grossawardvaluelc = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1u:nth-child(6)').text
        grossawardvaluelc = grossawardvaluelc.replace(',','')
        grossawardvaluelc = float(grossawardvaluelc)
    except:
        pass
    try:
        award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1S:nth-child(5) span').text
        award_date = datetime.strptime(award_date,'%d-%b-%Y').strftime('%Y/%m/%d')
    except:
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.x1w:nth-child(8) > a').click()
        notice_data.notice_url = page_main.current_url
        time.sleep(3)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#plMain > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
        
    try:
        publish_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Contract Date")]//following::td[1]').text
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass 
    
#     # Onsite Field -Selection Method
#     # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Selection Method")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'EN'
    # Onsite Field -Country
    # Onsite Comment -1.csv file is pulled name as "mfa_csrn_ca_countrycode.csv"	2."Hong Kong, China=CN" and "Regional=PH"

        try:
            customer_details_data.org_country = org_country
        except Exception as e:
            logging.info("Exception in org_country: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Executing Agency
    # Onsite Comment -None

        customer_details_data.org_name = org_name

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    # Onsite Field -Project Name
    # Onsite Comment -None

        lot_details_data.lot_number=1
        lot_details_data.lot_title = notice_data.local_title
	notice_data.is_lot_default = True


        award_details_data = award_details()

        # Onsite Field -Consultant Name
        # Onsite Comment -None

        award_details_data.bidder_name = bidder_name

        # Onsite Field -Contract Amount (USD)
        # Onsite Comment -None

        award_details_data.grossawardvaluelc = grossawardvaluelc

        # Onsite Field -Contract Date
        # Onsite Comment -None

        award_details_data.award_date = award_date

        # Onsite Field -Country of Incorporation
        # Onsite Comment -1.csv file is pulled name as "mfa_csrn_ca_countrycode.csv"	2."Hong Kong, China=CN" and "Regional=PH"

        award_details_data.bidder_country = page_main.find_element(By.XPATH, '//*[contains(text(),"Country of Incorporation")]//following::td[1]').text
        if 'Regional' in award_details_data.bidder_country:
            award_details_data.bidder_country  = 'PH'
        elif 'China' in  award_details_data.bidder_country or 'Hong Kong' in award_details_data.bidder_country:
            award_details_data.bidder_country = 'CN'
        else:
            award_details_data.bidder_country = fn.procedure_mapping("assets/mfa_csrn_ca_countrycode.csv",award_details_data.bidder_country )
            # Onsite Field -Address
            # Onsite Comment -None

        award_details_data.address = page_main.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::td[1]').text

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
    
    clk=page_main.find_element(By.XPATH,'//button[@id="bBack"]').click()
    time.sleep(10)
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://selfservice.adb.org/OA_HTML/OA.jsp?OAFunc=XXCRS_LOACSC_HOME_PAGE"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

	try:
	    for page_no in range(2,10):
		page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/span[2]/div/div[3]/table[2]/tbody/tr/td/span/table/tbody/tr[2]/td/div/span/table/tbody/tr/td[3]/span[1]/table[2]/tbody/tr'))).text
		rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/span[2]/div/div[3]/table[2]/tbody/tr/td/span/table/tbody/tr[2]/td/div/span/table/tbody/tr/td[3]/span[1]/table[2]/tbody/tr')))
		length = len(rows)
		for records in range(1,length):
		    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/span[2]/div/div[3]/table[2]/tbody/tr/td/span/table/tbody/tr[2]/td/div/span/table/tbody/tr/td[3]/span[1]/table[2]/tbody/tr')))[records]
		    extract_and_save_notice(tender_html_element)
		    if notice_count >= MAX_NOTICES:
			break
	
		    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
		        break
	                    
	        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
	            break
	
	        try:   
	            next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
	            page_main.execute_script("arguments[0].click();",next_page)
	            logging.info("Next page")
	            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/span[2]/div/div[3]/table[2]/tbody/tr/td/span/table/tbody/tr[2]/td/div/span/table/tbody/tr/td[3]/span[1]/table[2]/tbody/tr'),page_check))
	        except Exception as e:
	            logging.info("Exception in next_page: {}".format(type(e).__name__))
	            logging.info("No next page")
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
