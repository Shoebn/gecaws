from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bd_cptu_spn"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bd_cptu_spn"
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
    notice_data.script_name = 'bd_cptu_spn'

    notice_data.main_language = 'EN'
    

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BD'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BDT'

#after opening the url insert date in both this field "div:nth-child(8) > div > div > div"  and then click on "Search".

    # Onsite Field -Title & Reference No.
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Issue Date
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Last Selling
    # Onsite Comment -None

    try:
        document_purchase_start_time = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
        document_purchase_start_time = re.findall('\d+/\d+/\d{4}',document_purchase_start_time)[0]
        notice_data.document_purchase_start_time = datetime.strptime(document_purchase_start_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_start_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Title & Reference No.
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#bodyContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -None
    # Onsite Comment -1.if in this field written as "Request for Expressions of Interest" then take notice_type=5.Otherwise take it notice_type=4.

    try:
        notice_type = page_details.find_element(By.CSS_SELECTOR, 'h5 > b:nth-child(1)').text
        if "Expressions of Interest" in notice_type:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

    # Onsite Field -KEY INFORMATION >> Procurement Method or KEY INFORMATION >> Procurement Sub-Method
    # Onsite Comment -1.in the given field written as "NCT" then take "procurement_method=0","ICT" then take "procurement_method=1" otherwise take "procurement_method=2"
    #ref_url:1)https://cptu.gov.bd/advertisement-goods/details-83109.html	2)https://cptu.gov.bd/advertisement-works/details-83116.html	3)https://cptu.gov.bd/advertisement-services/Civil-Estimator-(AutoCAD-Operator)---8348.html
    try:
        procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"KEY INFORMATION")]//following::td[1]').text
        if 'NCT' in procurement_method:
            notice_data.procurement_method = 0
        elif 'ICT' in procurement_method:
            notice_data.procurement_method = 1
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -EOI Ref. No.
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"EOI Ref. No.")]//following::td[1]').text
    except:
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation Reference No")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

    # Onsite Field -Invitation For
    # Onsite Comment -1.replace folloeing keyword with given keyword("Goods=Supply","Works=Works","Services=Service")
    #ref_url:"https://cptu.gov.bd/advertisement-goods/details-83112.html"

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Invitation For")]//following::td[1]').text
        if 'Goods' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        if 'Works' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        notice_data.contract_type_actual = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:              
        funding_agencies_data = funding_agencies()
        
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Development Partner")]//following::td[1]').text.split("(")[1].split(")")[0].strip()
        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/bd_cptu_spn_fundingagencycode.csv",funding_agency)
        
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    
    try:
        project_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Project/Programme Name")]//following::td[1]').text
        if project_name!="":
            notice_data.project_name = project_name
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass
    # Onsite Field -Tender Package No
    # Onsite Comment -None
    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package No")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Closing Date and Time
    # Onsite Comment -None
    #ref_url:"https://cptu.gov.bd/advertisement-goods/details-83112.html"

    try:
        document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Closing Date and Time")]//following::td[1]').text
        document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
        notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
    except:
        try:
            document_purchase_end_time = page_details.find_element(By.XPATH, '//*[contains(text(),"EOI Closing Date and Time")]//following::td[1]').text
            document_purchase_end_time = re.findall('\d+/\d+/\d{4}',document_purchase_end_time)[0]
            notice_data.document_purchase_end_time = datetime.strptime(document_purchase_end_time,'%d/%m/%Y').strftime('%Y/%m/%d')
        except Exception as e:
            logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
            pass
  
    # Onsite Field -Tender Opening Date and Time
    # Onsite Comment -None

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Opening Date and Time")]//following::td[1]').text
        document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Place/Date/Time of Tender Meeting (Optional):
    # Onsite Comment -1.split between "Date" and "Time".

    try:
        pre_bid_meeting_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Place/Date/Time of Tender Meeting (Optional)")]//following::td[1]').text
        pre_bid_meeting_date = re.findall('\d+/\d+/\d{4}',pre_bid_meeting_date)[0]
        notice_data.pre_bid_meeting_date = datetime.strptime(pre_bid_meeting_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in pre_bid_meeting_date: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Place/Date/Time of Tender Meeting (Optional):
    # Onsite Comment -1.split between "Date" and "Time".
    #ref_url:"https://cptu.gov.bd/advertisement-goods/details-83112.html"
    try:
        notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Eligibility of Tenderer ")]//following::td[1]').text
    except:
        try:
            notice_data.eligibility = page_details.find_element(By.XPATH, '//*[contains(text(),"Experience, Resources and Delivery Capacity Required")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in eligibility: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Experience, Resources and Delivery Capacity Required
    # Onsite Comment -None
    #ref_url:"https://cptu.gov.bd/advertisement-services/Innovation-and-Commecialization-Specialist--8349.html"
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    # Onsite Field -Brief Description of Goods or Works :
    # Onsite Comment -None
    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender Lot Information >> Security Amount
    # Onsite Comment -None

    try:
        notice_data.earnest_money_deposit = page_details.find_element(By.CSS_SELECTOR, '#bodyContent tr:nth-child(32) > td > table > tbody > tr > td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in earnest_money_deposit: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -None
#ref_url:1)"https://cptu.gov.bd/advertisement-goods/details-83112.html"	2)"https://cptu.gov.bd/advertisement-services/Innovation-and-Commecialization-Specialist--8349.html".

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#bodyContent'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'BD'
            customer_details_data.org_language = 'EN'
        # Onsite Field -None
        # Onsite Comment -None

            customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

            try:
                customer_details_data.org_city = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.add this both field in org_address "//*[contains(text(),"Ministry/Division")]//following::td[1]" and "//*[contains(text(),"Agency")]//following::td[1]".

            try:
                customer_details_data.org_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Ministry/Division")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Procuring Entity Code
        # Onsite Comment -None

            try:
                customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Entity Code")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Name of Official Inviting Tender :  or  Name of Official Inviting EOI
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Official Inviting Tender :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Address of Official Inviting Tender :   or   Address of Official Inviting EOI
        # Onsite Comment -None

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address of Official Inviting Tender  :")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Phone" and "Fax".

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Details of Official Inviting Tender :")]//following::td[1]').text.split("Phone:")[1].split(", Fax:")[0]
            except:
                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact details of Official Inviting EOI")]//following::td[1]').text.split("Tele: ")[1].split(",, Fax")[0]
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Fax" and "Email"

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Details of Official Inviting Tender :")]//following::td[1]').text.split("Fax:")[1].split(", Email:")[0]
            except:
                try:
                    customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact details of Official Inviting EOI")]//following::td[1]').text.split("Fax :")[1].split(", Email :")[0]
                except Exception as e:
                    logging.info("Exception in org_fax: {}".format(type(e).__name__))
                    pass
        
        # Onsite Field -None
        # Onsite Comment -1.split after "Email".

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact Details of Official Inviting Tender :")]//following::td[1]').text.split("Email: ")[1].strip()
            except:
                try:
                    customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact details of Official Inviting EOI")]//following::td[1]').text.split(", Email :")[1].strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_number = 1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#bodyContent > div > div.panel-body.table-responsive > table > tbody > tr:nth-child(32) > td > table > tbody > tr'):
            lot_details_data = lot_details()
        # Onsite Field -Invitation For
        # Onsite Comment -1.replace folloeing keyword with given keyword("Goods=Supply","Works=Works","Services=Service")
            lot_details_data.lot_number = lot_number
            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Invitation For
        # Onsite Comment -None

            try:
                lot_details_data.lot_contract_type_actual = notice_contract_type
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Lot Information >> Lot No
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Tender Lot Information >> Identification
        # Onsite Comment -None

            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
        
        # Onsite Field -Tender Lot Information >> Completion Time in Weeks/Months
        # Onsite Comment -None

            try:
                lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
            
            lot_number +=1
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
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
    urls = ["https://cptu.gov.bd/advertisement-notices/notice-search.html"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        th1 = str(th)
        th1 = datetime.strptime(th1,'%Y-%m-%d').strftime('%d/%m/%Y')
        today1 = date.today()
        today = str(today1)
        today = datetime.strptime(today,'%Y-%m-%d').strftime('%d/%m/%Y')
        yest_date = page_main.find_element(By.XPATH,'//*[@id="inputissueDateFrom"]').send_keys(th1)
        today_date = page_main.find_element(By.XPATH,'//*[@id="inputissueDateTo"]').send_keys(today)
        
        search =WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search"]/div[9]/div/button[1]')))
        page_main.execute_script("arguments[0].click();",search) 

        try:
            for page_no in range(1,3):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr[1]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
                try:   
                    next_page = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="search"]/div[11]/div[2]/ul/li[2]/button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 80).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/section[2]/section/div/div/div[2]/form/div[10]/table/tbody/tr[1]'),page_check))
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
