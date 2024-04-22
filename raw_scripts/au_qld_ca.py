from gec_common.gecclass import *
import logging
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


#Note:First click on "View Tenders >> Awarded" than second click on droup down "Sorting By: >> Awarded Date"
#Note:If tender_html_element page in this "table:nth-child(5) tr > td:nth-child(2) > font > b" selector have this keywod "Awarded" than only grab tha data


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_qld_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'au_qld_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'AUD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -Note:If tender_html_element page in this "table:nth-child(5) tr > td:nth-child(2) > font > b" selector have this keywod "Awarded" than only grab tha data
    notice_data.notice_type = 7
    
    # Onsite Field -Request No.
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) > b').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Note:Take a text
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.ID, '#MSG').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date >> released
    # Onsite Comment -Note:Grab also time

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(4) > span.SUMMARY_OPENINGDATE").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Date >> awarded
    # Onsite Comment -Note:Grab also time

    try:
        notice_data.tender_award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span:nth-child(11)').text
    except Exception as e:
        logging.info("Exception in tender_award_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.ID, '#MSG').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
    try:
        notice_data.notice_text += page_details.find_element(By.ID, '#main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -Note:Notice_no teke from url....Ex,.("https://qtenders.epw.qld.gov.au/qtenders/tender/display/tender-details.do?CSRFNONCE=D2E89309F96E84042E60EB9B828A5BCD&id=49836&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3D18AF686D420CBFEC64F8406800135A08%26amp%3Baction%3Dadvanced-tender-search-awarded-tender%26amp%3BchangeLevel%3D%26amp%3Binputlist%3DhasETB%26amp%3BorderBy%3DawardedDate%26amp%3BwithdrawalReason%3D%26amp%3BexpiredReason%3D%26amp%3BtenderState%3D%26amp%3BtenderId%3D%26amp%3Bpage%3D1" thke only "49836")

    try:
        notice_data.notice_no = page_details.find_element(By.ID, '#MSG').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Overview")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Overview
    # Onsite Comment -Note:Take a first data

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Overview")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Note:Splite after "UNSPSC" this keyword... Take a all data
    try:
        notice_data.category = page_details.find_element(By.CSS_SELECTOR, "tr:nth-child(1) > td:nth-child(2) > table:nth-child(5)").text
        cpv_codes = fn.CPV_mapping("assets/au_qld_ca_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Mega Category
    # Onsite Comment -Note:If not present then pass autocpv
    try:
        notice_data.category = page_details.find_element(By.XPATH, "//*[contains(text(),"Mega Category")]//following::td[1]").text
        cpv_codes = fn.CPV_mapping("assets/au_qld_ca_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of Work
    # Onsite Comment -Note:Repleace following keywords with given keywords("Works=Works","Goods and Services=Supply and Service") 	Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

    try:
        notice_data.notice_contract_type = page_details1.find_element(By.XPATH, '//*[contains(text(),"Type of Work")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of Work
    # Onsite Comment -Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

    try:
        notice_data.contract_type_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),"Type of Work")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Total Value of the Contract
    # Onsite Comment -Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

    try:
        notice_data.est_amount = page_details1.find_element(By.XPATH, '//*[contains(text(),"Total Value of the Contract")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Total Value of the Contract
    # Onsite Comment -Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

    try:
        notice_data.grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),"Total Value of the Contract")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass

    # Onsite Field -Period Contract
    # Onsite Comment -Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

    try:
        notice_data.contract_duration = page_details1.find_element(By.XPATH, '//*[contains(text(),"Period Contract")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass    
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.ID, '#main'):
            customer_details_data = customer_details()
        # Onsite Field -Status & Type	Details
        # Onsite Comment -Note:Splite after "Issued by" or "UNSPSC"

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'table:nth-child(5) tr td:nth-child(3) > span').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Still need help? Contact Us
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(7) tr > td:nth-child(1) tr > td  tr:nth-child(1) > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Splite after PHONE / PHONE(icon)

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(7) tr > td:nth-child(1) > table > tbody').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Splite after email(icon)

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(7) tr > td:nth-child(1) > table > tbody a').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address
        # Onsite Comment -Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'table:nth-child(5)  tr'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -Note:Take a text

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.ID, '#MSG').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Contractors
        # Onsite Comment -Note:Click on "tr:nth-child(2) > td:nth-child(2) > h3 > span > a" this selector on page_detail than grab the data

            try:
                for single_record in page_details1.find_elements(By.XPATH, '//*[contains(text(),"Contractors")]//following::table[1]'):
                    award_details_data = award_details()
		
                    # Onsite Field -Contractors
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"1)")]//following::td[1]|//*[contains(text(),"2)")]//following::td[1]|//*[contains(text(),"3)")]//following::td[1]|//*[contains(text(),"4)")]//following::td[1]|//*[contains(text(),"5)")]//following::td[1]').text
			
                    # Onsite Field -Contractors
                    # Onsite Comment -None

                    award_details_data.address = page_details1.find_element(By.XPATH, '//*[contains(text(),"1)")]//following::td[3]|//*[contains(text(),"2)")]//following::td[3]|//*[contains(text(),"3)")]//following::td[3]|//*[contains(text(),"4)")]//following::td[3]|//*[contains(text(),"5)")]//following::td[3]').text
			
                    # Onsite Field -Contractors
                    # Onsite Comment -None

                    award_details_data.grossawardvaluelc = page_details1.find_element(By.XPATH, '//*[contains(text(),"1)")]//following::td[5]|//*[contains(text(),"2)")]//following::td[5]|//*[contains(text(),"3)")]//following::td[5]|//*[contains(text(),"4)")]//following::td[5]|//*[contains(text(),"5)")]//following::td[5]').text
			
                    # Onsite Field -Date >> awarded
                    # Onsite Comment -None

                    award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span:nth-child(11)').text
			            
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
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
page_details1 = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://qtenders.epw.qld.gov.au/qtenders/tender/search/tender-search.do?action=advanced-tender-search-awarded-tender&orderBy=closeDate&CSRFNONCE=3915E437651493117E23FAF983855B97"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,6):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="hcontent"]//following::tr[not(@style="display:none")]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hcontent"]//following::tr[not(@style="display:none")]')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hcontent"]//following::tr[not(@style="display:none")]')))[records]
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

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="hcontent"]//following::tr[not(@style="display:none")]'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details1.quit()
    
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)