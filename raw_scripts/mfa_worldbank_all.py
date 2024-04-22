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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "mfa_worldbank_all"
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
    notice_data.script_name = 'mfa_worldbank_all'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Country
    # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

    try:
        notice_data.performance_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_countrycode.csv",notice_data.notice_data.performance_country)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Project Title
    # Onsite Comment -None

    try:
        notice_data.project_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Notice Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Notice Type
    # Onsite Comment -1.replace grabbed keywords with given numbers ("Invitation for Bids=4","Goods and Works Award=4","Small Contracts Award=4","Consultant Award=4","Request for Expression of Interest=5","Contract Award=7","General Procurement Notice=2","Invitation for Prequalification=6").

    try:
        notice_data.notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Language
    # Onsite Comment -None

    try:
        notice_data.main_language = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_languagecode.csv",notice_data.notice_data.main_language)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in main_language: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Published Date
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
    
    # Onsite Field -Description
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.project_par.parsys').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Notice No
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice No")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Borrower Bid Reference
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Borrower Bid Reference")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Submission Deadline Date/Time
    # Onsite Comment -1.don't take notice_deadline for notice_type=7.

    try:
        notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),"Submission Deadline Date/Time")]//following::p[1]").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in None.find_elements(By.None, 'None'):
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = '1012'
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    



#format-1)"td:nth-child(4)" in this field  (Invitation for Bids","Goods and Works Award","Small Contracts Award","Consultant Award","Request for Expression of Interest","General Procurement Notice","Invitation for Prequalification") keywords are present.
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Overview")]//following::section[1]'):
            customer_details_data = customer_details()
        # Onsite Field -Country
        # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

            try:
                customer_details_data.org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
		        cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_countrycode.csv",customer_details_data.org_country)
        	    for cpv_code in cpv_codes:
            		cpvs_data = cpvs()
           		    cpvs_data.cpv_code = cpv_code
            		cpvs_data.cpvs_cleanup()
            		notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Language
        # Onsite Comment -None

            try:
                customer_details_data.org_language = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        	    cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_languagecode.csv",customer_details_data.org_language)
        	    for cpv_code in cpv_codes:
            		cpvs_data = cpvs()
            		cpvs_data.cpv_code = cpv_code
            		cpvs_data.cpvs_cleanup()
            		notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in org_language: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Organization/Department
        # Onsite Comment -1.if org_name is blank then pass "The World Bank" as org_name static. and then also add new field "org_parent_id" and in this field pass "1012" static.

            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organization/Department")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"CONTACT INFORMATION")]//following::p[2]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -City
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"City")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Postal Code
        # Onsite Comment -None

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Code")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Email
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"CONTACT INFORMATION")]//following::p[9]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Website
        # Onsite Comment -None

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -ref_url:"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00258336"
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#overview > div > div > div:nth-child(2) > div.col-md-8.col-xs-12 > div > section'):
            lot_details_data = lot_details()
        # Onsite Field -Description of Goods / Service
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > table:nth-child(9) > tbody > tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Quantity required
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > table:nth-child(9) > tbody > tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Physical unit
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > table:nth-child(9) > tbody > tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass





#format-2)"td:nth-child(4)" in this field  "Contract Award" keyword is present.

#check comments for additional changes
#1)for bidder name
# As discussed with shoeib added below condition .. (1) if lot avaialble than condition 
# lot_title ="blank "and award_details ="blank" []
# than lot_details =[]
# (2) if lots not avaible than
# award_details= []
# and lot_details= []


    # Onsite Field -Scope of Contract: 			1.split after "Scope of Contract:".
    # Onsite Comment -1.split after "Scope of Contract:".

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Scope of Contract: ")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Scope of Contract: ")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            customer_details_data = customer_details()
        # Onsite Field -Country
        # Onsite Comment -1.replace following countries with given keyword(West Bank and Gaza,OECS Countries,Andean Countries,Western and Central Africa,Eastern and Southern Africa,Pacific Islands,World,Middle East and North Africa,Latin America,Latin America and Caribbean,Multi-Regional,Africa,Western Africa,Eastern Africa,Europe and Central Asia,South East Asia,East Asia and Pacific,South Asia = US)

            try:
                customer_details_data.org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
		        cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_countrycode.csv",customer_details_data.org_country)
        	    for cpv_code in cpv_codes:
            		cpvs_data = cpvs()
           		    cpvs_data.cpv_code = cpv_code
            		cpvs_data.cpvs_cleanup()
            		notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Language
        # Onsite Comment -None

            try:
                customer_details_data.org_language = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        	    cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_languagecode.csv",customer_details_data.org_language)
        	    for cpv_code in cpv_codes:
            		cpvs_data = cpvs()
            		cpvs_data.cpv_code = cpv_code
            		cpvs_data.cpvs_cleanup()
            		notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in org_language: {}".format(type(e).__name__))
                pass
        
            customer_details_data.org_name = 'The World Bank'
            customer_details_data.org_parent_id = '1012'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split between "Final Evaluation Price" and "Signed Contract Price".		2.here "XAF 7856000" take "XAF" in currency.		3.ref_url"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00244835"

    try:
        notice_data.currency = page_details.find_element(By.XPATH, '//*[contains(text(),"Final Evaluation Price")]').text
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split after "Signed Contract price"		2.here "XOF 48479120" take only "XOF" in "currency"		3.ref_url:"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00258422"

    try:
        notice_data.currency = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    



# Onsite Field -None
# Onsite Comment -1.ref_url"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00244835"

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.ref_url"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00244835"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#overview > div > div > div:nth-child(2) > div.col-md-8.col-xs-12 > div > section'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Firm(s):")]//following::b[1]').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split after "Country:".

                    award_details_data.bidder_country = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(1) > div').text
                    cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_countrycode.csv",award_details_data.bidder_country)
                    for cpv_code in cpv_codes:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = cpv_code
                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
			
                    # Onsite Field -Date Notification of Award Issued
                    # Onsite Comment -1.split after "Date Notification of Award Issued"

                    award_details_data.award_date = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(1)').text
			
                    # Onsite Field -Duration of Contract
                    # Onsite Comment -1.split after "Duration of Contract".

                    award_details_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split between "Final Evaluation Price" and "Signed Contract Price".		2.here "XAF 7856000" take "7856000" in final_estimated_value.

                    award_details_data.final_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Final Evaluation Price")]').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split after "Signed Contract Price".		2.here "XAF 7856000" take "7856000" in grossawardvaluelc.

                    award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Signed Contract Price")]').text
			
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


# Onsite Field -None
# Onsite Comment -1.ref_url"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00244835"

    try:              
        for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -Description
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.ref_url:"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP00258422"

            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#overview > div > div > div:nth-child(2) > div.col-md-8.col-xs-12 > div > section'):
                    award_details_data = award_details()
		
                    # Onsite Field -None
                    # Onsite Comment -None
                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Bidder(s):")]//following::b[1]').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split after "Country:".
                    award_details_data.bidder_country = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(1) > div').text
                    cpv_codes = fn.CPV_mapping("assets/mfa_worldbank_all_countrycode.csv",award_details_data.bidder_country)
                    for cpv_code in cpv_codes:
                        cpvs_data = cpvs()
                        cpvs_data.cpv_code = cpv_code
                        cpvs_data.cpvs_cleanup()
                        notice_data.cpvs.append(cpvs_data)
			
                    # Onsite Field -None
                    # Onsite Comment -1.split between "Awarded Bidder(s):" and "Country:".
                    award_details_data.address = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(1) > div').text
                   
                    # Onsite Field -Date Notification of Award Issued
                    # Onsite Comment -1.split after "Date Notification of Award Issued"
                    award_details_data.award_date = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(1)').text
			
                    # Onsite Field -Duration of Contract
                    # Onsite Comment -1.split after "Duration of Contract".
                    award_details_data.contract_duration = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split after "Evaluated Bid Price".		2.here "XOF 48479120" take only "48479120" in "final_estimated_value"
                    award_details_data.final_estimated_value = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(2)').text
			
                    # Onsite Field -None
                    # Onsite Comment -1.split after "Signed Contract price"		2.here "XOF 48479120" take only "48479120" in "grossawardvaluelc"
                    award_details_data.grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(4)').text
			
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://projects.worldbank.org/en/projects-operations/procurement?srce=both"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,20):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr'),page_check))
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
    
    output_json_file.copyFinalJSONToServer(output_json_folder)