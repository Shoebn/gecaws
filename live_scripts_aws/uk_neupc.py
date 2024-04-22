from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_neupc"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_neupc"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Take "Competitive Contract Notice" and " Contract Notice"----4 ","Competitive Contract Award Notice" and "Contract Award Notice"-----7 (CA)", "Competitive Contract Notice Addendum----16 (AMD)"
    # Onsite Comment -None
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if 'competitive contract notice' in notice_type.lower() and 'contract notice' in notice_type.lower():
            notice_data.notice_type = 4
        elif 'competitive contract award notice' in notice_type.lower() and 'contract award notice' in notice_type.lower():
            notice_data.notice_type = 7 
        elif 'competitive contract notice addendum' in notice_type.lower():
            notice_data.notice_type = 16
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'GBP'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'uk_neupc'
    
    # Onsite Field -Published
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td.sorting_1").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    # Onsite Field -Notice Type
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    # Onsite Field -View 
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -Description
    # Onsite Comment -split data from "Description" to "CPV Codes:"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
    
    try:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Description')[1].split('\n')[0]
    except:
        try:
            notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Short description:')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass
        

    
    # Onsite Field -None
    # Onsite Comment -None
    
    # Description split 
    try:
        if 'Reference number' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
            notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Reference number: ')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
	    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Description')[1].split('\n')[0]
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
	    
    try:
        if 'programme financed by european Union funds' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.lower():
            if 'yes'in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split(' programme financed by European Union funds:')[1].split('\n')[0].strip().lower():
                funding_agencies_data = funding_agencies()
                funding_agencies_data.funding_agencies = 1344862
                funding_agencies_data.funding_agencies_cleanup()
                notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass
    # Onsite Field -None
    # Onsite Comment -None

    try: 
        customer_details_data = customer_details()
        # Onsite Field -Organisation Name
        # Onsite Comment -None

        try:
            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
    
        # Onsite Field -None
        # Onsite Comment -split data from "Awarding Authority:" to "Tel"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
        
        try:
            if 'United Kingdom' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
                org_address = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Awarding Authority:')[1].split('\n')[1:3] 
                customer_details_data.org_address = ' '.join(org_address) 
            elif 'United Kingdom' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('address')[1].split('Tel')[0]:
                org_address = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('address')[1].split('Tel')[0].split('\n')[1:]
                customer_details_data.org_address = ' '.join(org_address) 
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
    

        # Onsite Field -Tel
        # Onsite Comment -split data from "Tel" to "Email"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
        
        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Tel.')[1].split(',')[0].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Tel
        # Onsite Comment -split data from "Email" to "URL"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
        
        try:
            customer_details_data.org_email = fn.get_email(page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text) 
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        try:
            if 'To respond to this opportunity, please click here:' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p > a').text.split('To respond to this opportunity, please click here:')[0]
                
            elif 'please click here:' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
                customer_details_data.org_website = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p > a').text.split('please click here:')[0]
                
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'

    
        # Onsite Field -Nuts Codes
        # Onsite Comment -split data from "Nuts Codes" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"

      
        try:
            customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('NUTS Codes :')[1].split('\n')[1].split(' ')[0]
        except:
            try:
                customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Nuts code:')[1].split('\n')[1].split(' ')[0]
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            # Onsite Field -Contact
            # Onsite Comment -split data from "Contact" to "Main Address"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=789190047"
        
        if 'Contact' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Contact:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -Contact Type -----"Services as Services"
    # Onsite Comment -split data from "Contact Type" to "Sub Type"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791657484"
    try:
        if 'service' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split(' Contract Type:')[1].split('\n')[0].strip().lower():
            notice_data.notice_contract_type = 'Service'
        elif 'works' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split(' Contract Type:')[1].split('\n')[0].strip().lower():
            notice_data.notice_contract_type = 'Works'
        elif 'supply' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split(' Contract Type:')[1].split('\n')[0].strip().lower():
            notice_data.notice_contract_type = 'Supply'
        elif 'consultancy' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split(' Contract Type:')[1].split('\n')[0].strip().lower():
            notice_data.notice_contract_type = 'Consultancy'
        elif 'non consultancy' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split(' Contract Type:')[1].split('\n')[0].strip().lower():
            notice_data.notice_contract_type = 'Non consultancy'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -vat
    # Onsite Comment -split data from "VAT:" to "Currency"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=789190047"
    try:
        if 'vat' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.lower():
            notice_data.vat = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('VAT:')[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -None
    # Onsite Comment -None
    
    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number =1
        # Onsite Field -Title
        # Onsite Comment -None
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        
        # Onsite Field -Description
        # Onsite Comment -split data from "Description" to "CPV Codes:"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
        try:
            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Description:')[1].split('\n')[0]
            except:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Short description:')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
    
    
    
        # Onsite Field -Estimated Value of Requirement
        # Onsite Comment -split data from " Estimated Value of Requirement:" to "Currency"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
        try:
            lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Estimated Value of Requirement:')[1].split('\n')[0] 
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -None

        try:
            # Onsite Field -None
            # Onsite Comment -split data from "9. Awarded to:" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791657484"
            if 'Awarded to' in page_details.find_element(By.CSS_SELECTOR, '#mainContent > div.pure-g').text:
                award_details_data = award_details()
                award_details_data.bidder_name = page_details.find_element(By.CSS_SELECTOR, '#mainContent > div.pure-g').text.split('Awarded to:')[1].split('\n')[2] 
        
                # Onsite Field -split data from "Value Cost:" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791657484"
                # Onsite Comment -None

                # award_details_data.grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, '#mainContent > div.pure-g').text.split('Value Cost:')[1].split('\n')[0]
        
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None
        # Onsite Comment -split data from "9. Start:" to "End"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=789190047", "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791657484"
        try:
            if 'start' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.lower():
                try:
                    contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Start:')[1].split('\n')[0].split('/ End')[0].strip()
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    contract_start_date = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Start date:')[1].split('\n')[0].split('/ End')[0].strip()
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass
        # Onsite Field -None
        # Onsite Comment -split data from "End:" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=789190047", "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791657484"
        if 'end' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.lower():
            try:
                contract_end_date = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('End date:')[1].split('\n')[0].strip()
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
    
        # Onsite Field -NUTS Code
        # Onsite Comment -split data from "NUTS Code" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=790928531"
        if 'nuts codes' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.lower():
            
            try:
                lot_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('NUTS Codes :')[1].split('\n')[1].split(' ')[0]
            except:
                try:
                    lot_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Nuts code:')[1].split('\n')[1].split(' ')[0]
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
    
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Date of dispatch of this notice
    # Onsite Comment -split data from "Date of dispatch of this notice" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=790928531"
    if 'Date of dispatch of this notice' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
        try:
            dispatch_date = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Date of dispatch of this notice:')[1].split('\n')[0].strip()
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Procedure Type
    # Onsite Comment -split data from "Procedure Type" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=790928531", "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791739575"
    if 'Procedure Type' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Procedure Type:')[1].split('\n')[0]
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:  
        if 'Award criteria' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
            for single_record in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Award criteria:')[1].split('II.2.11) Information about options')[0].split('\n'):
                # Onsite Field -Award criteria:
                # Onsite Comment -split data from "Award criteria:" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=790928531"
                if 'criterion - name:' in single_record.lower():
                    tender_criteria_data = tender_criteria()
                    tender_criteria_data.tender_criteria_title = single_record.split('/')[0]
                    tender_criteria_data.tender_criteria_weight = int(single_record.split('Weighting: ')[1])
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
    # Onsite Comment -split data from "Delta eSourcing portal at:" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=789190047"
    try:
        if 'Delta eSourcing portal at' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
            notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('Delta eSourcing portal at:')[1].split('\n')[1] 
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -split data from "To view this notice" --- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
    try:
        if 'To view this notice' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text:
            notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('To view this notice')[1].split('\n')[1]
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None
    try:     
        if 'cpv codes' in page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.lower():
            cpv_row = page_details.find_element(By.CSS_SELECTOR, 'div > div.completeentry > p').text.split('CPV Codes')[1].split('NUTS Codes')[0]
            for single_record in cpv_row.split('\n')[1:-2]:
            # Onsite Field -CPV
            # Onsite Comment -split data from "CPV Codes" to "NUTS Code"--- ref. url "https://neupc.delta-esourcing.com/commonNoticeSearch/viewNotice.html?displayNoticeId=791072590"
                if len(single_record)>4:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = re.findall('\d+',single_record)[0]
                    cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
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
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://neupc.delta-esourcing.com/commonNoticeSearch/noticeSearchResults.html'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        for page_no in range(2,4):
            page_check =  WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.basic-table.dataTable.no-footer tbody:nth-child(2) > tr.odd:nth-child(1)'))).text
            rows =WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tbody > tr')))[records]
                extract_and_save_notice(tender_html_element)
                
                if notice_count >= MAX_NOTICES:
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'table.basic-table.dataTable.no-footer tbody:nth-child(2) > tr.odd:nth-child(1)'),page_check))
            except Exception as e:
                logging.info("Exception in next_page: {}".format(type(e).__name__))
                logging.info("No next page")
                break
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    logging.info("Exception:"+str(e))
    raise e
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
