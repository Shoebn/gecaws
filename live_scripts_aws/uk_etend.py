from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_etend"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_etend"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -To get the data enter captcha in 'Please type the code shown below' field > search 
    notice_data.script_name = 'uk_etend'
    
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
    notice_data.currency = 'GBP'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -if document_type_description have keyword "Awarded" then notice type will be 7, and for "Cancelled"/"Terminated" notice type will be 16 and notice type will be 4 for others
   
    
    # Onsite Field -Status
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text
        if 'Tender Submission' in notice_data.document_type_description:
            notice_data.notice_type = 4
        elif 'Awarded' in notice_data.document_type_description:
            notice_data.notice_type = 7
        elif 'Cancelled' in notice_data.document_type_description or 'Terminated' in notice_data.document_type_description:
            notice_data.notice_type = 16     
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
   
    # Onsite Field -CfT Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CfT Title
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Date published
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Tenders Submission Deadline
    # Onsite Comment -take notice_deadline for notice_type 4 and 16 only

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procedure
    # Onsite Comment -None
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text.strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_etend_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated value
    # Onsite Comment -None

    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(11)').text
        grossbudgetlc1 = int(grossbudgetlc)
        notice_data.grossbudgetlc = float(grossbudgetlc1)
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated value
    # Onsite Comment -None

    try:
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Notice PDF'
    # Onsite Field -Notice PDF
    # Onsite Comment -None
        attachments_data.external_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(9) > a').get_attribute('href')        
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except:
        pass
    # Onsite Field -CfT Title
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
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.card-wrapper').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CfT CA Unique ID:
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"CfT CA Unique ID:")]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Type:
    # Onsite Comment -None

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Type:")]//following::dd[1]').text
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        if 'Supplies' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None
    try:              
        customer_details_data = customer_details()
    # Onsite Field -CA
    # Onsite Comment -None
        try:
            customer_details_data.org_name = org_name
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
    # Onsite Field -CONTACT POINT:
    # Onsite Comment -None
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Point:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
    # Onsite Field -NUTS CODES:
    # Onsite Comment -None
        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS codes:")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:              
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"CPV Codes:")]//following::dd[1]').text
        cpv = cpv_code.split("\n")
        for cpv_record in cpv:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_record.split("-")[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:              
    # Onsite Field -EU funding:
    # Onsite Comment -if in below text written as "EU funding: No  " than pass the "None " in field name "T.FUNDING_AGENCIES::TEXT" and if "EU funding: yes" than pass the "Funding agency" name as "European Agency (internal id: 1344862) " in field name "T.FUNDING_AGENCIES::TEXT"
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"EU funding:")]//following::dd[1]').text
        if 'Yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    if notice_data.notice_type == 4:
        try:
            lots = page_details.find_element(By.CSS_SELECTOR, 'div.card-wrapper').text.split('LOT N')
            lot_number = 1
            for lot in lots:
                if 'AME(' in lot:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number
                    try:
                        lot_title = lot.split('\n')[1].split('\n')[0]
                        lot = re.findall('\w+ \d+',lot_title)[0]
                        lot_details_data.lot_title = lot_title.split(lot)[1].strip()
                    except:
                        lot_details_data.lot_title = lot.split('\n')[1].split('\n')[0]
                    lot_details_data.lot_description = lot_details_data.lot_title
                    try:
                        lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -Procurement Type:
                    # Onsite Comment -None

                    lot_details_data.contract_type = notice_data.notice_contract_type
                    try:
                        lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract duration in months or years, excluding extensions:")]//following::dd[1]').text
                    except Exception as e:
                        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_details_data.lot_quantity_uom = page_details.find_element(By.XPATH, '//*[contains(text(),"Number Of Lots			:")]//following::dd[1]').text
                    except Exception as e:
                        logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                        pass                       

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    
    
    if notice_data.notice_type == 7 or notice_data.notice_type == 16:
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = notice_data.notice_title
        lot_details_data.lot_description = lot_details_data.lot_title
        notice_data.is_lot_default = True
        award_details_data = award_details()
            # Onsite Field -Estimated value
            # Onsite Comment -None
        try:
            grossawardvaluelc =  tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(11)').text
            award_details_data.grossawardvaluelc = float(grossawardvaluelc)
        except:
            pass
        # Onsite Field -Award date
        # Onsite Comment -None
        award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10)').text
        award_date = re.findall('\d+/\d+/\d{4}',award_date)[0]
        award_details_data.award_date = datetime.strptime(award_date,'%d/%m/%Y').strftime('%Y/%m/%d')
        
        award_details_data.award_details_cleanup()
        lot_details_data.award_details.append(award_details_data)
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    
    notice_data.tender_cleanup()
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
    
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    url = 'https://etendersni.gov.uk/epps/viewCFTSAction.do'
    fn.load_page(page_main, url, 50)
    logging.info('----------------------------------')
    logging.info(url)
    indexes = [3,5,8,9]
    for index in indexes:
        pp_btn = Select(page_main.find_element(By.ID,'Status'))
        pp_btn.select_by_index(index)
        search_btn = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,' input.btn.btn-primary.float-right')))
        page_main.execute_script("arguments[0].click();",search_btn)
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="T01"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="T01"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="nextNav"]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="T01"]/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            pass
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
