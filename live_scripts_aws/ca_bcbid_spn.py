from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_bcbid_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_bcbid_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ca_bcbid_spn'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'CAD'
   
    notice_data.procurement_method = 2
   
    notice_data.notice_type = 4
    
    # Onsite Field -Opportunity Description
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(5)').text
        notice_data.document_type_description = GoogleTranslator(source='ca', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Issue Date and Time(Pacific Time)
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "#body_x_grid_grd > tbody > tr > td:nth-child(6)").text
        publish_date = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Closing Date and Time(Pacific Time)
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "#body_x_grid_grd > tbody > tr > td:nth-child(7)").text
        notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Opportunity ID
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(2)').text
    except:
        try:
            notice_data.notice_no = notice_data.notice_url.split('/')[-1]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.wrapper').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    time.sleep(3)
    # Onsite Field -Summary Details
    # Onsite Comment -if Summary Details not available then take local_title.

    try:
        local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Summary Details')]//following::div[1]").text
        if local_description != '':
            notice_data.local_description = local_description
            notice_data.notice_summary_english = GoogleTranslator(source='ca', target='en').translate(local_description) 
        else:
            notice_data.local_description = None
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Estimated Contract Duration (in months)
    # Onsite Comment -None  #body_x_tabc_rfp_ext_prxrfp_ext_x_placeholder_rfp_220801064436 > tbody > tr:nth-child(2) > td > div > div > div

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[@id="body_x_tabc_rfp_ext_prxrfp_ext_x_txtRfpEstDuration"]').get_attribute('value')
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        for single_record in page_details.find_elements(By.XPATH, '/html/body/form[1]/div[3]/div/main/div[2]/div[2]/div[3]/div/div[2]/table/tbody/tr/td/div/table/tbody/tr/td[1]/div/table/tbody/tr/td/div/div[1]/div/div/div/table/tbody/tr/td[2]/div/table/tbody/tr[2]/td/div/div/div[2]/table/tbody/tr/td/div/div/div/div/div/div/div[1]/div/table/tbody/tr/td[3]/div/div/div[3]/div/ul/li/div/a'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258"

            attachments_data.file_name = single_record.text.split(".")[0]
            
#              Onsite Field -None  #body_x_tabc_rfp_ext_prxrfp_ext_x_prxDoc_x_grid_grd__ctl2_files_x_btnDownload_6BBE4087-4ACB-4292-BA9E-D3669AB6A00F
#         Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258"

            attachments_data.external_url = single_record.get_attribute('href')
            
        # Onsite Field -None
        # Onsite Comment -1.reference url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175258" 			2.split file_type. eg., here "Appendix C_Submission Declaration Form.docx" take ".docx" in file_type.

            try:
                attachments_data.file_type = single_record.text.split(".")[-1]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
      
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None                                         div.panel-content > nav > ul > li:nth-child(2) > div
# Onsite Comment -1.take customer_details after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details.

    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.panel-content > nav > ul > li:nth-child(2) > div")))
        page_details.execute_script("arguments[0].click();",click)
    except:
        pass
    time.sleep(5)
    try:
        holder = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="body_x_tabc_rfpAdditional RFx Info_prxrfpAdditional RFx Info_x_placeholder_rfp_200117182437"]/div[1]/div/h2')))
    except:
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'CA'
        customer_details_data.org_language = 'EN'
        # Onsite Field -Organization (Issued by)
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, '#body_x_grid_grd > tbody > tr > td:nth-child(11)').text
            
        # Onsite Field -None  #body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_grid_rfp_200524212531_grd > tbody > tr > td.center.aligned
        # Onsite Comment -1.take contact_person after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.in contact_person take only names. eg., here "Nimmi	Takkar	Nimmi.Takkar@gov.bc.ca" take "Nimmi	Takkar" in contact_person. remove space. 				3.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175260".

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_grid_rfp_200524212531_grd > tbody > tr').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -None  #body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_placeholder_rfp_200528045945 > tbody > tr:nth-child(2) > td.iv-phc-cell.bottom.aligned.center.aligned > div > div > div
        # Onsite Comment -1.take org_email after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.in org_email take only email id. eg., here "Nimmi	Takkar	Nimmi.Takkar@gov.bc.ca" take "Nimmi.Takkar@gov.bc.ca" in org_email. 				3.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/175260".

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[@id="body_x_tabc_rfpAdditional RFx Info_prxrfpAdditional RFx Info_x_grid_rfp_200524212531_grd"]/tbody/tr/td[3]').text
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH,'//*[@id="body_x_tabc_rfpAdditional RFx Info_prxrfpAdditional RFx Info_x_txtRfpContactAlternateEmail"]').get_attribute('value')
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
            
        # Onsite Field -Regions
        # Onsite Comment -1.take org_state after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176263"

        try:
            customer_details_data.org_state = page_details.find_element(By.XPATH, "//*[contains(text(),'Regions')]//following::div[2]").text
        except Exception as e:
            logging.info("Exception in org_state: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Postal Code
        # Onsite Comment -1.take postal_code after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176263"

        try:
            customer_details_data.postal_code = page_details.find_element(By.CSS_SELECTOR, "#body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_address_rfp_200825104610_x_txtZip").get_attribute("value")
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Office Street Address
        # Onsite Comment -1.take org_address after clicking on "div.panel-content > nav > ul > li:nth-child(2) > div" in page_details. 				2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176263"

        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, "#body_x_tabc_rfpAdditional\ RFx\ Info_prxrfpAdditional\ RFx\ Info_x_address_rfp_200825104610_x_txtVoie").get_attribute("value")
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
        try:
            click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.panel-content > nav > ul > li:nth-child(1) > div")))
            page_details.execute_script("arguments[0].click();",click)
            time.sleep(5)
        except:
            pass
    
        try:
            holder = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#body_x_tabc_rfp_ext_prxrfp_ext_x_phcInfo > div.frame.header > div > h2')))
        except:
            pass
        time.sleep(5)
        
        # Onsite Field -Official Contact Details
        # Onsite Comment -1.split org_phone between "Phone: " and "Fax: ".	2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176356".

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Official Contact Details')]//following::textarea").text.split("Phone: ")[1].split("Fax:")[0]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Official Contact Details
        # Onsite Comment -1.split org_fax after "Fax: ".		2.reference_url "https://www.bcbid.gov.bc.ca/page.aspx/en/bpm/process_manage_extranet/176356".

        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH, "//*[contains(text(),'Official Contact Details')]//following::div").text.split("Fax:")[1].strip()
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
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
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.bcbid.gov.bc.ca/page.aspx/en/rfp/request_browse_public"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(1,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body_x_grid_grd"]/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="body_x_grid_grd"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                    
                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#body_x_grid_PagerBtnNextPage")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(5)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="body_x_grid_grd"]/tbody/tr'),page_check))
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
