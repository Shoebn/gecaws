from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "uk_publiccosct"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_publiccosct"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'uk_publiccosct'

    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GBP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#maintablecontent tr td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
        
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Title:")]//following::td[1]').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference No:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
        
    
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
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Deadline Date:")]//following::td[1]').text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice Type:")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -In detail page click on "Introduction" and select data
# Onsite Comment -None

    try:              
        for single_record in page_details.find_elements(By.XPATH, "//a[contains(@title, 'Download')]"):
            attachments_data = attachments()
            
            attachments_data.external_url = 'https://www.publiccontractsscotland.gov.uk/search/show/search_view.aspx?ID='+str(notice_data.notice_no)
            
            try:
                file_type =  attachments_data.external_url
                if '.pdf' in file_type or '.PDF' in file_type:
                    attachments_data.file_type = 'pdf'
                elif '.doc' in file_type:
                     attachments_data.file_type = 'doc'
                elif '.xml' in file_type:
                    attachments_data.file_type = 'xml'
                elif '.html' in file_type:
                    attachments_data.file_type = 'html'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.file_name = single_record.text
       
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    

    
    try:
        clk1 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="Tab2"]')))
        page_details.execute_script("arguments[0].click();",clk1)
    except:
        pass
    
    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Value excluding VAT: ")]').text.split(':')[1].split('GBP')[0].strip()
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(' ',''))
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duration in months:")]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::p[1]').text
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Information about European Union funds")]//following::p[1]').text.split(':')[1]
        if 'Yes' in source_of_funds:
            notice_data.source_of_funds = 'International agencies'
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 7794645
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in source_of_funds: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Short description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.4) Short description")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.3) Type of contract")]//following::p[1]').text
        if 'Services' in notice_contract_type:
            
            notice_data.notice_contract_type = 'Service'
        else:
            notice_data.notice_contract_type = notice_contract_type
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of dispatch")]//following::p[1]').text
        dispatch_date = re.findall('\d+/\d+/\d{4}',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#ctl00_ContentPlaceHolder1_tab_StandardNoticeView1_RadMultiPage1').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
 
  
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
        
        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::p[1]').text
        except:
            try:
                customer_details_data.org_name = tender_html_element.text.split('Published By:')[1].split('\n')[0].strip()   
            except Exception as e:
                    logging.info("Exception in org_name: {}".format(type(e).__name__))
                    pass
        
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"I.1) Name and addresses")]//following::div [1]').text.split('Telephone')[0]
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone:")]').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address:")]').text.split('Main address:')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]').text.split(':')[1].strip()
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS:")]').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact person")]').text.split(':')[1]
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        lot_number = 1
        lot_details_data = lot_details()
        lot_details_data.lot_number = lot_number
        try:
            lot_details_data.lot_title = notice_data.notice_title
            notice_data.is_lot_default = True
        except Exception as e:
            logging.info("Exception in lot_title: {}".format(type(e).__name__))
            pass
        

        try:
            lot_details_data.lot_description = notice_data.local_description
        except Exception as e:
            logging.info("Exception in lot_description: {}".format(type(e).__name__))
            pass
        
        try:
            lot_details_data.lot_grossbudget_lc = notice_data.grossbudgetlc
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        try:
            lot_details_data.lot_nuts = customer_details_data.customer_nuts
        except Exception as e:
            logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
            pass
        
        
        try:
            lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duration in months:")]').text
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try:
            contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Start:")]').text.split(':')[1]
            contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
            lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

        
        try:
            contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"End:")]').text.split(':')[1]
            contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
            lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass
        
        try:
            lot_cpvs_data = lot_cpvs()
            lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::p[1]').text
            lot_cpvs_data.lot_cpvs_cleanup()
            lot_details_data.lot_cpvs.append(lot_cpvs_data)
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass
        

    
        lot_details_data.lot_details_cleanup()
        notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Award criteria
# Onsite Comment -None

    try:      
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"II.2.5) Award criteria")]//following::p'):
            if 'Weighting' in single_record.text:
                tender_criteria_data = tender_criteria()
                tender_criteria_data.tender_criteria_title = single_record.text.split('criterion:')[1].split('/ Weighting:')[0].strip()
                if 'Price' in tender_criteria_data.tender_criteria_title:
                    tender_criteria_data.tender_is_price_related = True
                else:
                    tender_criteria_data.tender_is_price_related = False
                
                try:
                    tender_criteria_data.tender_criteria_weight = int(single_record.text.split('/ Weighting:')[1].strip())
                except Exception as e:
                    logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                    pass
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
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
page_details =fn.init_chrome_driver(arguments) 
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
        pp_btn.select_by_index(1) 
        
        try:
            clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_maincontent_btnSearch')))
            page_main.execute_script("arguments[0].click();",clk)
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
