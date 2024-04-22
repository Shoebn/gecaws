from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bd_egp"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
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
SCRIPT_NAME = "bd_egp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'bd_egp'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BD'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'BDT'
    
    
    notice_data.notice_type = 4
    
    # Onsite Field -Tender/Proposal ID
    # Onsite Comment -... Just take tender number  eg-"863696" from the data

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(2)').text.split(",")[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Nature, Title    ......."Goods - Supply" "Works - Works" "
    # Onsite Comment -just take "Procurement Nature" eg "good, services'

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3)').text.split(",")[0].strip()
        if "Works" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        elif "Goods" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title
    # Onsite Comment -remove url just use title

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(3) a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#resultTable td:nth-child(4)').text
    except:
        pass
    
    # Onsite Field -Publishing Date and Time,
    # Onsite Comment -just split "Publishing Date and Time," from the data

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable td:nth-child(6)").text.split(",")[0]
        publish_date = re.findall('\d+-\w+-\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date and Time
    # Onsite Comment -just split " Closing Date and Time" from the data

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable td:nth-child(6)").text.split(",")[1]
        notice_deadline = re.findall('\d+-\w+-\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
     # Onsite Field -just take the title which is the url for detail page
    # Onsite Comment -None
    
    try: 
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR,'#resultTable td:nth-child(3) a').click()
        time.sleep(4)
        page_main.switch_to.window(page_main.window_handles[1]) 
        time.sleep(4)
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' span.t-align-left')))
        notice_data.notice_url = url 
        logging.info(notice_data.notice_url)
    except:
        pass
           
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#frmviewForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

#     # Onsite Field -Procurement Type 
#     # Onsite Comment -if given as"NCT" take as "0"

    try:
        procurement_method = page_main.find_element(By.XPATH, "//*[contains(text(),'Procurement Type ')]//following::td[1]").text
        if "NCT" in procurement_method:
            notice_data.procurement_method = 0
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Event Type :
#     # Onsite Comment -None

    try:
        notice_data.document_type_description = page_main.find_element(By.XPATH, "//*[contains(text(),'Event Type')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.CSS_SELECTOR, "table:nth-child(5) > tbody > tr:nth-child(2) > td:nth-child(2)").text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Category
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

   # Onsite Field -Project Name :
    # Onsite Comment -None

    try:
        notice_data.project_name = page_main.find_element(By.XPATH, "//*[contains(text(),'Project Name')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Pre - Tender/Proposal meeting Start
    # Onsite Comment -None

    try:
        pre_bid_meeting_date = page_main.find_element(By.XPATH, "//*[contains(text(),'Pre - Tender/Proposal meeting Start')]//following::td[1]").text
        pre_bid_meeting_date = re.findall('\d+-\w+-\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -split data from Tender/Proposal Opening Date and Time :" till "Last Date and Time for Tender/Proposal Security"
    # Onsite Comment -None

    try:
        document_opening_time = page_main.find_element(By.CSS_SELECTOR, 'table:nth-child(5) > tbody > tr:nth-child(6) > td:nth-child(4)').text
        document_opening_time = re.findall('\d+-\w+-\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d-%b-%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Category
    # Onsite Comment -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"

    try:
        notice_data.category = page_main.find_element(By.XPATH, "//*[contains(text(),'Category')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Eligibility of Tenderer :
    # Onsite Comment -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"

    try:
        notice_data.eligibility = page_main.find_element(By.XPATH, "//*[contains(text(),'Eligibility of Tenderer')]//following::td[1]").text
    except Exception as e:
        logging.info("Exception in eligibility: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender/Proposal Document Price (In BDT) :
    # Onsite Comment -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"

    try:
        document_cost = page_main.find_element(By.XPATH, "//*[contains(text(),'Proposal Document Price')]//following::td[1]").text
        notice_data.document_cost = float(document_cost)
    except Exception as e:
        logging.info("Exception in document_cost: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.earnest_money_deposit = page_main.find_element(By.CSS_SELECTOR, " table.tableList_1 > tbody > tr:nth-child(2) > td:nth-child(4)").text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()
        # Onsite Field -Ministry, Division, Organization, PE
        # Onsite Comment -None

        customer_details_data.org_name = org_name

        
        # Onsite Field -Name of Official Inviting
        # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Name of Official Inviting")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        # Onsite Field -Address
        # Onsite Comment -None

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::td[1]').text.split("Address : ")[1]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -City
        # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"City")]//following::td[1]').text.split(":")[1].strip()
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Phone No
        # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Phone No")]//following::td[1]').text.split(":")[1].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Fax No
        # Onsite Comment -None

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Fax No")]//following::td[1]').text.split(":")[1].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'BD'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -ref url "https://www.eprocure.gov.bd/resources/common/ViewTender.jsp"
# # Onsite Comment -None

    try:       
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, ' table.tableList_1 > tbody > tr:nth-child(n)')[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Lot No.
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Identification of Lot
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -Tentative Start Date
        # Onsite Comment -None

            try:
                contract_start_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                contract_start_date = re.findall('\d+-\w+-\d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tentative Completion Date
        # Onsite Comment -None

            try:
                contract_end_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
                contract_end_date = re.findall('\d+-\w+-\d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
            except Exception as e:
                logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
        lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

        # Onsite Field -Development Partner :
        # Onsite Comment -None

    try:
        funding_agency = page_main.find_element(By.XPATH, "//*[contains(text(),'Development Partner ')]//following::td[1]").text
        funding_agency = GoogleTranslator(source='auto', target='en').translate(funding_agency)
        if 'yes' in funding_agency:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass

    try:              
        attachments_data = attachments()
        # Onsite Field -Documents
        # Onsite Comment -None

        external_url = page_main.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > a')
        page_main.execute_script("arguments[0].click();",external_url)
        time.sleep(5)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])

        attachments_data.file_type = ".pdf"

        attachments_data.file_name = "Documents"


        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    page_main.close()
    page_main.switch_to.window(page_main.window_handles[0])
    
    try:
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' th:nth-child(2)')))
    except:
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
page_main = Doc_Download.page_details 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.eprocure.gov.bd/resources/common/StdTenderSearch.jsp?h=t"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,100):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="resultTable"]/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultTable"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="resultTable"]/tbody/tr')))[records]
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#btnNext")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultTable"]/tbody/tr[2]'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
