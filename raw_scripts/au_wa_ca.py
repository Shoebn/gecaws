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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_wa_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'au_wa_ca'
    
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
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -Note:If notice_no is not present than take from notice_url in page_detail

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td.left.top > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -Note:Take a text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4) > a:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4) > a:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),'Description')])[2]//following::tr[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '(//*[contains(text(),'Description')])[2]//following::tr[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UNSPSC
    # Onsite Comment -Note:Split after "UNSPSC" this keyword
    try:
        notice_data.category = page_details.find_element(By.XPATH, "//*[contains(text(),'UNSPSC')]//following::td[1]").text
        cpv_codes = fn.CPV_mapping("assets/au_wa_ca_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Award Date
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        publish_date = page_details1.find_element(By.XPATH, "//*[contains(text(),'Award Date')]//following::td[1]").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Type of Work
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data ....	Note:Repleace following keywords with given keywords("Goods & Services=Supply & Service" , "Works=Works")

    try:
        notice_data.notice_contract_type = page_details1.find_element(By.XPATH, '//*[contains(text(),'Type of Work')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of Work
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        notice_data.contract_type_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),'Type of Work')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Original Contract Value
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        notice_data.est_amount = page_details1.find_element(By.XPATH, '//*[contains(text(),'Original Contract Value')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Original Contract Value
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        notice_data.grossbudgetlc = page_details1.find_element(By.XPATH, '//*[contains(text(),'Original Contract Value')]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None
# Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=B965CE6F51658E1B879FB29630C5933C&id=58919&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3DF03E4477BA87739E4909B4D8D64D0714%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#hcontent > div.pcontent'):
            customer_details_data = customer_details()
        # Onsite Field -Details
        # Onsite Comment -Note: split data after "Issued by" till "UNSPSC:"

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4) > span').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Enquiries >> Person
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),'Person')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Enquiries >> Phone
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Phone')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

        # Onsite Field -Enquiries >> Mobile
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),'Mobile')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass            
        
        # Onsite Field -Tender >> Region/s
        # Onsite Comment -None

            try:
                customer_details_data.org_state = page_details.find_element(By.XPATH, '//*[contains(text(),'Region/s')]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_state: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_country = 'AU'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Download Documents
# Onsite Comment -Note:First goto "#RESPONDENT" this page than click on "Download for Information Only" then click on "Download Document"
# Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=B965CE6F51658E1B879FB29630C5933C&id=58881&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3DF03E4477BA87739E4909B4D8D64D0714%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
    try:              
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#requestButton'):
            attachments_data = attachments()
            attachments_data.file_name = 'Tender Document'
        # Onsite Field -Download Documents
        # Onsite Comment -None

            attachments_data.external_url = page_details1.find_element(By.CSS_SELECTOR, '#requestButton').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, '#tenderSearchResultsTable > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -Details
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4) > a:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass

                # Onsite Field -Tender Responses
                # Onsite Comment -Note:Data present than take 
                # Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=5BD990F5E357849CADFD473750CF8F63&id=59019&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3D5844D8F8E03854FA386363F91FAF43BB%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table:nth-child(12)'):
                    award_details_data = award_details()
		
                    # Onsite Field -Tender Responses >> Businesses
                    # Onsite Comment -Note:Data present than take 

                    award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(12) tr > td:nth-child(1)').text
			
                    # Onsite Field -Tender Responses >> Prices
                    # Onsite Comment -Note:Data present than take 

                    award_details_data.grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(12) tr > td:nth-child(2)').text
			
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass



        #Format 2
        # Note:If "table:nth-child(12) tr:nth-child(5) > td:nth-child(1)" this selector bidder_name is present than do not grab that format-2 of award_details.

        
        # Onsite Field -None
        # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data
        # Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=5BD990F5E357849CADFD473750CF8F63&id=59019&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3D5844D8F8E03854FA386363F91FAF43BB%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
            try:
                for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#hcontent > div.pcontent'):
                    award_details_data = award_details()
		
                    # Onsite Field -Contractors
                    # Onsite Comment -Note:If "table:nth-child(12) tr:nth-child(5) > td:nth-child(1)" this selector bidder_name is present than do not grab that format-2 of award_details.
                    award_details_data.bidder_name = page_details1.find_element(By.CSS_SELECTOR, '//*[contains(text(),'Contractors')]//following::div[1]').text
			
                    # Onsite Field -Contractors
                    # Onsite Comment -None

                    award_details_data.address = page_details1.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div:nth-child(2)').text
			
                    # Onsite Field -Award Date
                    # Onsite Comment -None

                    award_details_data.award_date = page_details1.find_element(By.CSS_SELECTOR, '//*[contains(text(),'Award Date')]//following::td[1]').text
			
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
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.wa.gov.au/watenders/tender/search/tender-search.do?CSRFNONCE=F19F6CD1D35E5A7AF1161CD22B5C319B&noreset=yes&action=do-advanced-tender-search"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,5):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tenderSearchResultsTable"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tenderSearchResultsTable"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tenderSearchResultsTable"]/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tenderSearchResultsTable"]/tbody/tr'),page_check))
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
    page_details.quit() 
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)