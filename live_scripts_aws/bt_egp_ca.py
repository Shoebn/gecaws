from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "bt_egp_ca"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "bt_egp_ca"
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
    notice_data.script_name = 'bt_egp_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BT'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'BTN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -split only notice_no  for ex."15763, VEhicle maintenance", here take only "15763"  ,    split the data before comma

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a > p').text.split(',')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -split only related_id  for ex."16176, NCOA/ADM/23-24/804", here take only "NCOA/ADM/23-24/804" , take the data after comma

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3) > a > p').text.split(',')[1]
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass


    # Onsite Field -Value (In Nu.)
    # Onsite Comment -None

    try:
        notice_data.est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
        notice_data.est_amount = float(notice_data.est_amount )
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Value (In Nu.)
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass    
  
    # Onsite Field -Tender ID, Ref No., Title & Advertisement Date
    # Onsite Comment -None

    try:
        id1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) a').get_attribute("onclick").split("('")[1].split("',")[0]
        notice_url= 'https://www.egp.gov.bt'+str(id1)+''
        notice_data.notice_url=notice_url.replace(' ','')
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        notice_data.notice_url=url
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of Advertisement:")]//following::td[1]').text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'body > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    

#     # Onsite Field -Tender Package Description:
#     # Onsite Comment -None

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package Description:")]//following::td[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


#     # Onsite Field -Contract Award for:
#     # Onsite Comment -Replace following keywords with given respective keywords ('Services = service' , 'Goods = supply' , 'Works   = Works')

    
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award for:")]//following::td[1]').text
        if 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Goods' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Supply'
        elif 'Services' in notice_data.contract_type_actual :
            notice_data.notice_contract_type = 'Service'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Tender Package Description:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Tender Package Description:
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
   
        customer_details_data = customer_details()
    # Onsite Field -Hierarchy Node
    # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text


    # Onsite Field -Procuring Agency, Procurement Method
    # Onsite Comment -remove procurement_method from selector  for ex. "National Centre for Organic Agriculture OTM"   , here split only "National Centre for Organic Agriculture"

        try:
            customer_details_data.org_address = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        customer_details_data.org_language = 'EN'
        customer_details_data.org_country = 'BT'
    # Onsite Field -Procuring Agency Dzongkhag / District:
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Procuring Agency Dzongkhag / District")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass


    # Onsite Field -AGENCY DETAILS >> Name of Authorized Officer:
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of Authorized Officer:")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    try:
        funding_agency = page_details.find_element(By.XPATH, '//*[contains(text(),"Development Partner (if applicable):")]//following::td[1]').text
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
    
   
        
# # Onsite Field -None
# # Onsite Comment -None

    try:
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body  table:nth-child(8)'):
                lot_number=1
                if 'Tender Lot No.' in single_record.text:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number=lot_number

        # Onsite Field -Tender Lot No. and Description:
        # Onsite Comment -take only lot_detail , ref_url : "https://www.egp.gov.bt/resources/common/ViewContracts.jsp?contractNo=9789,%3Cbr%3E%3C/a%3E%20MoESD/Pro-21/2023-24/462.&pkgLotId=24595&tenderid=16417&userId=10077"
                    
                    lot_details_data.lot_title = single_record.find_element(By.XPATH, '//*[contains(text(),"Tender Lot No. and Description:")]//following::td[1]').text
                    lot_details_data.lot_title_english = lot_details_data.lot_title
                    try:
                        lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Award for:")]//following::td[1]').text
                        if 'Works' in lot_details_data.lot_contract_type_actual:
                            lot_details_data.contract_type = 'Works'
                        elif 'Goods' in lot_details_data.lot_contract_type_actual :
                            lot_details_data.contract_type = 'Supply'
                        elif 'Services' in lot_details_data.lot_contract_type_actual :
                            lot_details_data.contract_type = 'Service'
                    except Exception as e:
                        logging.info("Exception incontract_type: {}".format(type(e).__name__))
                        pass        


    #         # Onsite Field -Date of Contract Signing:
    #         # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewContracts.jsp?contractNo=10038,%3Cbr%3E%3C/a%3E%20BT-MoAF-317977-GO-RFQ&pkgLotId=24307&tenderid=16244&userId=5351"

                    try:
                        contract_start_date = single_record.find_element(By.XPATH, '//*[contains(text(),"Date of Contract Signing:")]//following::td[1]').text
                        contract_start_date  = re.findall('\d+-\w+-\d{4}',contract_start_date)[0]
                        lot_details_data.contract_start_date  = datetime.strptime(contract_start_date ,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except Exception as e:
                        logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                        pass

    #         # Onsite Field -Proposed Date of Contract Completion:
    #         # Onsite Comment -ref_url : "https://www.egp.gov.bt/resources/common/ViewContracts.jsp?contractNo=10038,%3Cbr%3E%3C/a%3E%20BT-MoAF-317977-GO-RFQ&pkgLotId=24307&tenderid=16244&userId=5351"
                    try:
                        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Proposed Date of Contract Completion:")]//following::td[1]').text
                        contract_end_date  = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
                        lot_details_data.contract_end_date  = datetime.strptime(contract_end_date ,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
                    except Exception as e:
                        logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                        pass

    #         # Onsite Field -INFORMATION ON AWARD
    #         # Onsite Comment -None

                    award_details_data = award_details()
                    # Onsite Field -Company Name of Bidder/Consultant:
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Company Name of Bidder/Consultant:")]//following::td[1]').text
                    # Onsite Field -INFORMATION ON AWARD >>   Contract Value (Nu.):
                    # Onsite Comment -None
                    try:
                        award_details_data.grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract Value (Nu.):")]//following::td[1]').text
                        award_details_data.grossawardvaluelc = float(award_details_data.grossawardvaluelc)
                    except:
                        pass
                    # Onsite Field -Date of Notification of Award
                    # Onsite Comment -None
                    try:
                        award_details_data.award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                        award_details_data.award_date = re.findall('\d+-\w+-\d{4}',award_details_data.award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_details_data.award_date,'%d-%b-%Y').strftime('%Y/%m/%d')
                    except:
                        pass
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)


                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1
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
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.egp.gov.bt/resources/common/AdvContractListing.jsp"] 
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
    
