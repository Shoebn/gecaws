from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_publiccosct_pp"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_publiccosct_pp"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'uk_publiccosct_pp'
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
 
    notice_data.currency = 'GBP'
    notice_data.procurement_method = 2

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#maintablecontent tr td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    
    # Onsite Field -In detail page click on "Introduction" and select data---Notice Type:
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Type:")]//following::td[1]').text
        if notice_data.document_type_description.startswith('01'):
            notice_data.notice_type = 2
        else:
            notice_data.notice_type = 3
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Introduction" and select data---Title:
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Title:")]//following::td[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Introduction" and select data---Publication Date:
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Publication Date:")]//following::td[1]').text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -In detail page click on "Introduction" and select data---Deadline date
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        notice_deadline = page_details.find_element(By.XPATH, '"//*[contains(text(),"Deadline Date:")]//following::td[1]"').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference No:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

   
    
    # Onsite Field -None
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_RadMultiPage1').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass

# Onsite Field -In detail page click on "Introduction" and select data
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, "//a[contains(@title, 'Download')]"):
            attachments_data = attachments()
        # Onsite Field -In detail page click on "Introduction" and select data for "external url"
        # Onsite Comment -if the src="/images/sitenoticeflag.gif" use the given format to grabe the data
            external_url = single_record.click()
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url= (str(file_dwn[0]))
            try:
                file_type =  attachments_data.external_url
                if '.pdf' in file_type or '.PDF' in file_type:
                    attachments_data.file_type = 'pdf'
                elif '.html' in file_type:
                    attachments_data.file_type = 'html'
                elif '.xml' in file_type:
                    attachments_data.file_type = 'xml'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        
        # Onsite Field -In detail page click on "Introduction" and select data for "file_name"
        # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data
            attachments_data.file_name = single_record.text
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -None
# Onsite Comment -None

    try:              
        lot_details_data = lot_details()
        lot_details_data.lot_number = 1
    # Onsite Field -In detail page click on "Introduction" and select data---Title:
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            lot_details_data.lot_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Title:")]//following::td[1]').text
        except:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        
    # Onsite Field -In detail page click on "Full Notice Text" and grab "Lot 1" and "Lot 2" and "Lot 3" in Lot_number  ---Short description of the contract or purchase(s)
    # Onsite Comment -if the src="/images/euroflag.gif"use the given format to grabe the data
        
        try:
            clk = WebDriverWait(page_details, 20).until(EC.element_to_be_clickable((By.LINK_TEXT,'Full Notice Text')))
            page_details.execute_script("arguments[0].click();",clk)
        except:
            pass
        time.sleep(5)
        
        try:
            lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS:")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -In detail page click on "Full Notice Text" and select data---II.1.4) Short description
    # Onsite Comment -if the src="/images/sitenoticeflag.gif" use the given format to grabe the data

        try:
            lot_details_data.lot_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Short description")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass

    # Onsite Field -In detail page click on "Full Notice Text" for "lot_grossbudgetlc" ---II.1.5) Estimated total value
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Value excluding VAT: ")]').text.split(':')[1].split('GBP')[0].strip()
            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(' ',''))
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Short description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Full Notice Text" for "grossbudgetlc" ---II.1.5) Estimated total value
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Value excluding VAT: ")]').text.split(':')[1].split('GBP')[0].strip()
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(' ',''))
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address:")]').text.split('Main address:')[1].strip()
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Full Notice Text" for "Dispatch_date" ---VI.5) Date of dispatch of this notice
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of dispatch")]//following::p[1]').text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass    
     
    # Onsite Field -In detail page click on "Full Notice Text" and select data---II.1.4) Short description-----split data between "II.1.4) Short description"and "II.1.6) Information about lots" in "local description"
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Short description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Full Notice Text" and select data---II.1.3) Type of contract
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p[1]').text.strip()
        if 'Services' in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        else:
            notice_data.notice_contract_type = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    
    # Onsite Field -None
# Onsite Comment -all flag have same "detail page" so "selector" is same for all

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
    # Onsite Field -In detail page click on "Full Notice Text" and select data---I.1) Name and addresses
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -just select address split data from "Name and addresses" till "Telephone"
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::div [1]').text.split('Telephone')[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -split data between "Telephone" and "Email" in "org_phone"
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone:")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -split data between "E-mail" and "NUTS" in org_email
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -split data between "NUTS" and "Internet address(es)" in customer_NUTS
    # Onsite Comment -if the src="/images/ftsnoticeflag.gif" use the given format to grabe the data

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS:")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -split data between "Contact person" and "Telephone" in contact_person
    # Onsite Comment -if the src="/images/sitenoticeflag.gif" use the given format to grabe the data

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact person")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.publiccontractsscotland.gov.uk/Search/Search_MainPage.aspx']
    
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        pp_btn = Select(page_main.find_element(By.CSS_SELECTOR,'#ctl00_maincontent_ddDocType'))
        pp_btn.select_by_index(2)
        
        try:
            search_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_maincontent_btnSearch')))
            page_main.execute_script("arguments[0].click();",search_clk)
        except:
            pass
        
        for page_no in range(1,75):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="maintablecontent"]/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="maintablecontent"]/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="maintablecontent"]/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="ctl00_maincontent_PagingHelperBottom_btnNext"]/i')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="maintablecontent"]/tbody/tr'),page_check))
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
    
