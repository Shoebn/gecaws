from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ac_ungm_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download
from selenium.webdriver.common.keys import Keys

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ac_ungm_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'ac_ungm_spn'
    notice_data.main_language = 'EN'
    notice_data.currency = 'USD'
    notice_data.procurement_method = 2
    
    # Onsite Comment -if 'document_type_description' have keyword 'Request for EOI' then notice type will be 5
#     notice_data.notice_type = 4
    
    # Onsite Field -Beneficiary country or territory

    try:
        performance_country_data = performance_country()
        p_country = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(8)').text
        performance_country_data.performance_country = fn.procedure_mapping("assets/us_ungm_countrycode.csv",p_country)
        if performance_country_data.performance_country == None:
            performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)
    except:
        performance_country_data = performance_country()
        performance_country_data.performance_country = 'US'
        notice_data.performance_country.append(performance_country_data)  
     
    
    try:
        notice_data.source_of_funds = 'International agencies'
        f_agenciess = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableCell.resultAgency span').get_attribute('innerHTML')
        if 'UN Secretariat' in f_agenciess or 'IRENA' in f_agenciess:
            f_agenciess = 'UNDP'
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = fn.procedure_mapping("assets/us_ungm_funding.csv",f_agenciess)
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -Type of opportunity

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(6)').text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
        if 'Request for EOI' in notice_data.document_type_description:
            notice_data.notice_type = 5
        else:
            notice_data.notice_type = 4
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(7)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        if len(notice_data.notice_title) < 5:
              notice_data.notice_title = notice_data.notice_no 
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.tableRow > div:nth-child(4)").text
        publish_date = re.findall('\d+-\w+-\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
  
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div.tableRow > div:nth-child(3)").text
        notice_deadline = re.findall('\d+-\w+-\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%b-%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableRow > div:nth-child(2) > div > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,180)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#centre > div > div').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::div").text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    

    try:              
        customer_details_data = customer_details()

        try:
            customer_details_data.org_name =tender_html_element.find_element(By.CSS_SELECTOR, 'div.tableCell.resultAgency span ').get_attribute('innerHTML')
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            customer_details_data.org_name = "United Nations Global Marketplace (UNGM)"
       

        customer_details_data.org_country = performance_country_data.performance_country

        try:
            contact_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#contacts')))
            page_details.execute_script("arguments[0].click();",contact_click)
            time.sleep(5)
        except:
            pass

        try:
            first_name = page_details.find_element(By.XPATH, '//*[contains(text(),"First name:")]//following::span[1]').text
            last_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Surname: ")]//following::span[1]').text
            customer_details_data.contact_person = first_name+' '+last_name
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone number:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass


        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email:")]//following::span[1]').text
        except:
            try:
                org_email = page_details.find_element(By.CSS_SELECTOR, '#contacts-tab > div').text 
                email_regex = re.compile(r"[\w\.-]+@[\w\.-]+")
                customer_details_data.org_email = email_regex.findall(org_email)[0]
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:
        Documents_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#documents')))
        page_details.execute_script("arguments[0].click();",Documents_click)
        time.sleep(5)
    except:
        pass

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.docslist div > span'):
            attachments_data = attachments()


            attachments_data.file_type = single_record.text.split('.')[-1]
        

        
            attachments_data.file_name = single_record.text.split('.')[0]


            external_url = single_record.find_element(By.CSS_SELECTOR, 'a')
            page_details.execute_script("arguments[0].click();",external_url)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    try:
        unspcs_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button#unspscs')))
        page_details.execute_script("arguments[0].click();",unspcs_click)
        time.sleep(3)
    
        cpv_at_source = ''
        unspcs_list_text = page_details.find_element(By.CSS_SELECTOR, '#unspscs-tab > div.unspscSelector > div.unspscTree').text
        unspcs_regex = re.compile(r'\d{8}')
        unspcs_list = unspcs_regex.findall(unspcs_list_text)

        for unspcs_code in unspcs_list:
            cpv_codes_list = fn.CPV_mapping("assets/mfa_ungm_cpv.csv",unspcs_code)
            for each_cpv in cpv_codes_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = each_cpv
                notice_data.class_at_source = 'CPV'
                cpv_at_source += each_cpv
                cpv_at_source += ','
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver_vpn(arguments)
page_main.maximize_window()
page_details = fn.init_chrome_driver_vpn(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.ungm.org/Public/Notice'] 
    for url in urls:
        fn.load_page(page_main, url, 150)
        logging.info('----------------------------------')
        logging.info(url)
        start_date = th.strftime('%d-%b-%Y')
        page_main.find_element(By.XPATH,'//*[@id="txtNoticePublishedFrom"]').send_keys(start_date)
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="txtNoticeDeadlineFrom"]').clear()
        time.sleep(3)
        page_main.find_element(By.XPATH,'//*[@id="lnkSearch"]').click()
        time.sleep(3)
        for scroll in  range(1,50):
            page_main.find_element(By.CSS_SELECTOR,'body').send_keys(Keys.END)
            time.sleep(5)

        try:
            page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tblNotices"]/div[2]/div'))).text
            rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblNotices"]/div[2]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblNotices"]/div[2]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
