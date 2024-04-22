from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_wa_ca"
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
import gec_common.Doc_Download
from selenium.webdriver.support.ui import Select

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_wa_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'au_wa_ca'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'AUD'
    
    notice_data.main_language = 'EN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    # Onsite Field -None
    # Onsite Comment -Note:If notice_no is not present than take from notice_url in page_detail

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.left.top > b').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Details
    # Onsite Comment -Note:Take a text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)  a').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "span.SUMMARY_CLOSINGDATE").text
        publish_date = re.findall('\d+ \w+, \d{4} \d+:\d+ [apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b, %Y %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Details
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > a:nth-child(1)').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#page-container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        local_description1 = page_details.find_element(By.XPATH, "(//*[contains(text(),'Description')])[2]//following::textarea").get_attribute("outerHTML")
        local_description = re.sub(r'<[^>]+>', '', local_description1)
        notice_data.local_description = local_description.replace("&lt;p&gt;",'').replace(";/p&gt;",'').replace("&lt","").replace("&nbsp;","")
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -UNSPSC
    # Onsite Comment -Note:Split after "UNSPSC" this keyword
    try:
        notice_data.category = page_details.find_element(By.XPATH, "(//*[contains(text(),'UNSPSC')])[2]//following::td[1]").text.split("-")[0].strip()
        cpv_codes = fn.CPV_mapping("assets/au_wa_ca_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    
#     # Onsite Field -Award Date
#     # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        contact_url = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details1,contact_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in contact_url: {}".format(type(e).__name__))
        
    
    # Onsite Field -Type of Work
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data ....	Note:Repleace following keywords with given keywords("Goods & Services=Supply & Service" , "Works=Works")
    
#     # Onsite Field -Type of Work
#     # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        notice_data.contract_type_actual = page_details1.find_element(By.XPATH, "//*[contains(text(),'Type of Work')]//following::td[1]").text
        if 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Original Contract Value
    # Onsite Comment -Note:Click in page_detail "tbody > tr > td:nth-child(1) > a" this selector than grab the data

    try:
        est_amount = page_details1.find_element(By.XPATH, "//*[contains(text(),'Original Contract Value')]//following::td[1]").text
        est_amount = re.sub("[^\d\.\,]", "", est_amount)
        notice_data.est_amount = est_amount.replace('.','').replace(',','').strip()
        notice_data.est_amount = float(notice_data.est_amount)
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

# Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=B965CE6F51658E1B879FB29630C5933C&id=58919&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3DF03E4477BA87739E4909B4D8D64D0714%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
    try:              
        customer_details_data = customer_details()
    # Onsite Field -Details
    # Onsite Comment -Note: split data after "Issued by" till "UNSPSC:"

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span').text.split("Issued by")[1].split("UNSPSC:")[0].strip()

    # Onsite Field -Enquiries >> Person
    # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Person')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Enquiries >> Phone
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Phone')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Enquiries >> Mobile
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Mobile')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass            

    # Onsite Field -Tender >> Region/s
    # Onsite Comment -None

        try:
            customer_details_data.org_state = page_details.find_element(By.XPATH, "//*[contains(text(),'Region/s')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Email')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_address = page_details1.find_element(By.XPATH, "//*[contains(text(),'Address')]//following::td[1]").text
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
            

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
        # Onsite Field -Details
        # Onsite Comment -None

        lot_details_data.lot_title = notice_data.local_title
        notice_data.is_lot_default = True
        lot_details_data.lot_title_english = notice_data.notice_title

        # Onsite Field -Tender Responses
        # Onsite Comment -Note:Data present than take 
        # Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=5BD990F5E357849CADFD473750CF8F63&id=59019&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3D5844D8F8E03854FA386363F91FAF43BB%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
        try:
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table:nth-child(12) tr')[4:]:
                award_details_data = award_details()

                # Onsite Field -Tender Responses >> Businesses
                # Onsite Comment -Note:Data present than take 

                award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                
                # Onsite Field -Tender Responses >> Prices
                # Onsite Comment -Note:Data present than take 

                grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
                grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace('.','').replace(',','').strip())

                award_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Date Awarded:')]//following::td[1]").text
                award_date = re.findall('\d+ \w+ \d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d %b %Y').strftime('%Y/%m/%d')

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
        except Exception as e:
            logging.info("Exception in award_details: {}".format(type(e).__name__))
            pass

        try:
            award_text = page_details.find_element(By.CSS_SELECTOR, "#hcontent > div.pcontent").text
            if "Businesses" not in award_text:
                award_details_data = award_details()

                # Onsite Field -Contractors
                # Onsite Comment -Note:If "table:nth-child(12) tr:nth-child(5) > td:nth-child(1)" this selector bidder_name is present than do not grab that format-2 of award_details.
                award_details_data.bidder_name = page_details1.find_element(By.XPATH, "//*[contains(text(),'Contractors')]//following::div[1]").text

                # Onsite Field -Contractors
                # Onsite Comment -None

                award_details_data.address = page_details1.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div:nth-child(2)').text
                
                # Onsite Field -Award Date
                # Onsite Comment -None

                award_date = page_details1.find_element(By.XPATH, "//*[contains(text(),'Award Date')]//following::td[1]").text
                award_date = re.findall('\d+ \w+, \d{4}',award_date)[0]
                award_details_data.award_date = datetime.strptime(award_date,'%d %b, %Y').strftime('%Y/%m/%d')

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
            lot_award_date = award_date
            lot_award_date = re.findall('\d+ \w+, \d{4}',lot_award_date)[0]
            lot_details_data.lot_award_date = datetime.strptime(lot_award_date,'%d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            pass

        if lot_details_data.award_details != []:
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -Download Documents
# Onsite Comment -Note:First goto "#RESPONDENT" this page than click on "Download for Information Only" then click on "Download Document"
# Ref_url=https://www.tenders.wa.gov.au/watenders/tender/display/tender-details.do?CSRFNONCE=B965CE6F51658E1B879FB29630C5933C&id=58881&action=display-tender-details&returnUrl=%2Ftender%2Fsearch%2Ftender-search.do%3FCSRFNONCE%3DF03E4477BA87739E4909B4D8D64D0714%26amp%3Bnoreset%3Dyes%26amp%3Baction%3Ddo-advanced-tender-search
    
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a#RESPONDENT")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(2)
    except:
        pass
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR," td:nth-child(1) > input.BUTTON")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(2)
    except:
        pass
    
    try:              
        attachments_data = attachments()
        attachments_data.file_name = 'Tender Document'
        # Onsite Field -Download Documents
        # Onsite Comment -None

        # Onsite Field -Download Documents
        # Onsite Comment -None

        attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'input#requestButton.SUBMIT').click()
        time.sleep(5)
        file_dwn = Doc_Download.file_download()
        attachments_data.external_url= (str(file_dwn[0]))

        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
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
page_main = fn.init_chrome_driver(arguments) 
page_details = Doc_Download.page_details
page_details.maximize_window()
page_details1 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(10)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenders.wa.gov.au/watenders/tender/search/tender-search.do?CSRFNONCE=89852903519DF05F17403954FDE16AC7&noreset=yes&action=do-advanced-tender-search"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"i.fa.fa-angle-down")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        select_fr = Select(page_main.find_element(By.CSS_SELECTOR,'select#state'))
        select_fr.select_by_value("Awarded")
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#btnAdvSarch")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(5)
        
        try:
            for page_no in range(2,5):#5
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
    
    page_details1.quit()
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
