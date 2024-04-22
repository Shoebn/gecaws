from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bt_egp_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.th_Doc_Download as Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bt_egp_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'bt_egp_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'IN'
    notice_data.performance_country.append(performance_country_data)
    

    
    # Onsite Field -None
    # Onsite Comment -if the following field  i.e ("Tender ID, Reference No, Public Status")  has  "Live" keyword  then take notice_type = 4  and the field has "Amendment/Corrigendum issued:" keyword then take notice_type 16
    notice_data.notice_type = 4
    
    # Onsite Field -Type, Method
    # Onsite Comment -take only procurment_method for ex."NCB", "ICB",     if "Type Method" has "ICB" then take procurment_method=1,  if "Type Method" has "NCB" then take procurment_method=0

    try:
        procurement_method = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        if 'NCB' in procurement_method:
            notice_data.procurement_method=0
        elif 'ICB' in procurement_method:
            notice_data.procurement_method=1
        else:
            pass
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender ID, Reference No, Public Status
    # Onsite Comment -take only  notice_no,  for ex."16909, MD/DzEHSS-20/2023-2024/1206, Live", here split only "16909, MD/DzEHSS-20/2023-2024/1206"

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -split only notice_contract_type   for ex. "Works (Small), Construction of Inclusive class room at Mongar Middle Secondary School" , here split only "Works" , i.e first word,               Replace following keywords with given respective keywords ('Works = Works' , 'Goods = Supply' , 'Services = Service')

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('(')[0]
        if 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Goods' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Supply'
        elif 'Services' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
#     # Onsite Field -Procurement Category, Title
#     # Onsite Comment -None

    
    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a > span > p').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Publishing Date & Time | Closing Date & Time
    # Onsite Comment -split only first line as a publish_date  for ex."09-Nov-2023 09:00 | 01-Dec-2023 09:30" , here take only "09-Nov-2023"

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.split('|')[0]
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Publishing Date & Time | Closing Date & Time
    # Onsite Comment -split only second line as a notice_deadline  for ex."09-Nov-2023 09:00 | 01-Dec-2023 09:30" , here take only "01-Dec-2023 09:30"

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#resultTable  td:nth-child(6)").text.split('|')[1]
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Procurement Category, Title
    # Onsite Comment -None

    try:
        notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a').get_attribute("onclick").split('id=')[1].split('&h=t')[0]
        notice_data.notice_url='https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id='+str(notice_url)+'&h=t'
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
#     # Onsite Field -Currency Name
#     # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16844&h=t" , if currency field is  not available then pass static as a "BTN"

    try:
        notice_data.currency = page_details.find_element(By.CSS_SELECTOR, '#tblCurrency  tr > td.t-align-left').text
    except Exception as e:
        notice_data.currency = 'BTN'
        logging.info("Exception in currency: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.ID, '#frmviewForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Document last selling / downloading Date and Time :
#     # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16919&h=t"

    try:
        document_purchase_end_time = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(4) tr:nth-child(5) > td:nth-child(4)').text
        document_purchase_end_time  = re.findall('\d+-\w+-\d{4}',document_purchase_end_time )[0]
        notice_data.document_purchase_end_time  = datetime.strptime(document_purchase_end_time ,'%d-%b-%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in document_purchase_end_time: {}".format(type(e).__name__))
        pass

#     # Onsite Field -Category :
#     # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16919&h=t"

    try:
        notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"Category : ")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
# # Onsite Field -None
# # Onsite Comment -None

            
    try:
        funding_agency = page_main.find_element(By.XPATH, "//*[contains(text(),'Development Partner :')]//following::td[1]").text
        if 'World Bank' in funding_agency:
            funding_agency = 1012
        elif 'Austrian Development Agency' in funding_agency:
            funding_agency = 7307798
        elif 'ADB' in funding_agency:
            funding_agency = 106

        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency= funding_agency

        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agency: {}".format(type(e).__name__))
        pass
            
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description ")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    
#     # Onsite Field -Brief Description of Goods and Related Service :
#     # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16911&h=t"

    try:
        notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Brief Description ")]//following::td[1]').text
        notice_data.notice_summary_english = notice_summary_english
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass

    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Procuring Agency :
    # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16914&h=t"

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Agency :")]//following::td[1]').text
        customer_details_data.org_country = 'BT'
        customer_details_data.org_language = 'EN'
    # Onsite Field -Name of Official Inviting Tender :
    # Onsite Comment -None

        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Official Inviting  Tender :")]//following::td[1]').text
            if ':' in contact_person:
                contact_person=contact_person.replace(':','')
            if contact_person == '':
                pass
            else:
                customer_details_data.contact_person =contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass


    # Onsite Field -Official Address :
    # Onsite Comment -None

        try:
            org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address ")]//following::td[1]').text
            if ':' in org_address:
                org_address=org_address.replace(':','')
            if org_address == '':
                pass
            else:
                customer_details_data.org_address = org_address
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass


    # Onsite Field -City
    # Onsite Comment -None

        try:
            org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"City")]//following::td[1]').text
            if ':' in org_city:
                org_city=org_city.replace(':','')
            if org_city == '':
                pass
            else:
                customer_details_data.org_city = org_city 
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Phone No
    # Onsite Comment -None

        try:
            org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone No")]//following::td[1]').text
            if ':' in org_phone:
                org_phone=org_phone.replace(':','')
            if org_phone == '':
                pass
            else:
                customer_details_data.org_phone = org_phone
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Fax No
    # Onsite Comment -None

        try:
            org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax No")]//following::td[1]').text
            if ':' in org_fax:
                org_fax=org_fax.replace(':','')
            if org_fax == '':
                pass
            else:
                customer_details_data.org_fax = org_fax

        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:        
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm > table.tableList_1'):
            if 'Lot' in single_record.text:
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
#         # Onsite Field -None
#         # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[1]').text
                    
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
        
#         # Onsite Field -Identification of Lot
#         # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"

                lot_details_data.lot_title = single_record.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[2]').text
                lot_details_data.lot_title_english =lot_details_data.lot_title
           
        
#         # Onsite Field -Contract Start Date
#         # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"

                try:
                    contract_start_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[5]').text
                    contract_start_date  = re.findall('\d+-\w+-\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date  = datetime.strptime(contract_start_date ,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass
        
#         # Onsite Field -Contract End Date
#         # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16842&h=t"

                try:
                    contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Lot No.")]//following::td[6]').text
                    contract_end_date  = re.findall('\d+-\w+-\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date  = datetime.strptime(contract_end_date ,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass
        
#         # Onsite Field -Procurement Category, Title
#         # Onsite Comment -split only notice_contract_type for ex. "Works (Small), Construction of Inclusive class room at Mongar Middle Secondary School" , here split only "Works" ,

                try:
                    lot_details_data.lot_contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text.split('(')[0]
                    if 'Works' in lot_details_data.lot_contract_type_actual:
                        lot_details_data.contract_type = 'Works'
                    elif 'Goods' in lot_details_data.lot_contract_type_actual :
                        lot_details_data.contract_type = 'Supply'
                    elif 'Services' in lot_details_data.lot_contract_type_actual :
                        lot_details_data.contract_type = 'Service'
                except Exception as e:
                    logging.info("Exception incontract_type: {}".format(type(e).__name__))
                    pass
        
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    
    
    
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name='Documents'
        external_url =  WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div/div[2]/input'))).click()
        time.sleep(5)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url = str(file_dwn[0])
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

# # Onsite Field -Information for Bidder/Consultant :
# # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewNotice.jsp?id=16907&h=t"

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#frmviewForm > table:nth-child(6)'):
            for i in single_record.text.split('\n'):
                if 'Evaluation' in i:
                    tender_criteria_data = tender_criteria()
                    tender_criteria_data.tender_criteria_title = i.split('(%) :')[0]
                    tender_criteria_data.tender_criteria_weight = int(i.split('(%) :')[1])
                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    
    # Onsite Field -Document Fees :
    # Onsite Comment -None

    try:
        notice_data.document_fee = page_details.find_element(By.XPATH, '//*[contains(text(),"Document Fees")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_fee: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.egp.gov.bt/resources/common/TenderListing.jsp?h=t"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="resultTable"]/tbody/tr'))).text
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
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="resultTable"]/tbody/tr'),page_check))
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
