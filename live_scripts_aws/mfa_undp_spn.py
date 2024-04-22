from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_undp_spn"
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
SCRIPT_NAME = "mfa_undp_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'mfa_undp_spn'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.source_of_funds = '7586854'
    
    # Onsite Comment -Note:If in this "td.content tr > td:nth-child(7)" selector have this keyword 
    #"RFQ - Request for quotation" take notice_type "4" , "EOI - Expression of interest" take notice_type "5" ,
    #"ITB - Invitation to bid" take notice_type "4" , "RFP - Request for proposal" take notice_type "4" , 
    #"IC - Individual contractor" take notice_type "4" , "ITP - Invitation to pre-qualify" take notice_type "5" ,
    #"RFI - Request for Information" take notice_type "5" , 
    #"CP-QB-FBS - Call for Proposal – Quality Based Fixed Budget" take notice_type "4" , 
    #"Innovation Challenge" take notice_type "4" , "Other" take notice_type "4".
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        if 'RFQ - Request for quotation' in notice_type or 'ITB - Invitation to bid' in notice_type or 'RFP - Request for proposal' in notice_type or 'IC - Individual contractor' in notice_type or 'CP-QB-FBS - Call for Proposal – Quality Based Fixed Budget' in notice_type or 'Innovation Challenge' in notice_type or 'Other' in notice_type:
            notice_data.notice_type = 4
        elif 'EOI - Expression of interest' in notice_type or 'ITP - Invitation to pre-qualify' in notice_type or 'RFI - Request for Information' in notice_type:
             notice_data.notice_type = 5
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -UNDP Country
    # Onsite Comment -Note:File_name=mfa_undp_spn_countrycode.csv
    try:
        country_data = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text.lower()
        performance_country_data = performance_country()
        if ', unscr' in country_data or '|' in country_data:
            country = country_data.split(', unscr')[0].split('|')[0].strip()
            
            country_code =fn.procedure_mapping("assets/mfa_undp_spn_countrycode.csv",country)
            performance_country_data.performance_country = country_code.upper()
            
        elif 'congo, dem. republic' in country_data:
            performance_country_data.performance_country = 'CD'
        else:
            country_code =fn.procedure_mapping("assets/mfa_undp_spn_countrycode.csv",country_data)
            performance_country_data.performance_country = country_code.upper()
            
        if performance_country_data.performance_country == None:
            performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)
    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Ref No
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Process
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Deadline 13-Feb-24 @ 07:00 AM (New York time)
    # Onsite Comment -Note:Grab time also
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(8)").text
        notice_deadline = re.findall('\d+-\w+-\d+ @ \d+:\d+ [PMAMpmam]+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%y @ %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Posted 31-Jan-24
    # Onsite Comment -Note:Grab time also

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9)").text
        publish_date = re.findall('\d+-\w+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except:
        pass
    # Onsite Field -Title
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'td.content').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        # Onsite Field -Period of assignment/services
        # Onsite Comment -Note:Splite after "Period of assignment/services" this keyword
        try:
            notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Period of assignment/services")]').text.split('Period of assignment/services')[1].strip()
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        # Onsite Comment -Note:Split between "Description of the Assignment: " and "Period of assignment" 
        try:
            notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'tr:nth-child(10) > td').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
        try:              
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 7586854
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        except Exception as e:
            logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
            pass
        
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = 'United Nations Development Programme'
            customer_details_data.org_parent_id = '7586854'
            customer_details_data.org_language = 'EN'
            
            try:
                customer_details_data.org_country = country_code.upper()
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass
            # Onsite Field -UNDP Office
            try:
                customer_details_data.org_address = org_address
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            # Onsite Field -Contact :
            # Onsite Comment -Note:Don't take in "<a>' tag data
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::td[1]').text.split('-')[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            # Onsite Field -Contact :
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::a[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        #Format 2 For Attachments
        # Ref_url=https://procurement-notices.undp.org/view_notice.cfm?notice_id=98159
        try:          
            Download = page_details.find_element(By.XPATH, '//*[contains(text(),"Documents :")]//parent::td')
            if 'Negotiation Document(s)' not in Download.text :

                for single_record in Download.find_elements(By.CSS_SELECTOR, 'a'):
                    attachments_data = attachments()
                    # Onsite Field -OriginalFileName
                    # Onsite Comment -Note:Don't take a file extention

                    attachments_data.file_name = single_record.text

                    attachments_data.external_url = single_record.get_attribute('href')

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized',"REDIRECT_ENABLED=True"]
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://procurement-notices.undp.org/index.cfm"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr')))
            length = len(rows)
            for records in range(1,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr')))[records]
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
