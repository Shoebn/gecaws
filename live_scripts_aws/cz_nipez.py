
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "cz_nipez"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "cz_nipez"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CZ'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'CZK'
    notice_data.main_language = 'CS'
    notice_data.procurement_method = 2
    
        
    status_text = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    if 'Cancelled' in status_text:
        notice_data.script_name = 'cz_nipez_amd'
        notice_data.notice_type = 16    
    else:
        notice_data.script_name = 'cz_nipez_spn'
        notice_data.notice_type = 4   
        
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass             
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass       

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_data.notice_deadline = datetime.strptime(notice_deadline, '%m/%d/%Y, %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)    
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass                 
        
    notice_data.notice_text += tender_html_element.get_attribute('outerHTML') 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")  
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep(5)
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass         
    
    try:
        Refuse_all_click_on_page_details = WebDriverWait(page_details, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Refuse all")]')))
        page_details.execute_script("arguments[0].click();",Refuse_all_click_on_page_details)
        logging.info("Refuse_all_click_on_page_details")            
    except Exception as e:
        logging.info("Exception in Refuse_all_click_on_page_details: {}".format(type(e).__name__))
        pass               
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Public contract regime")]//following::p[1]').text  
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass         
    
    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated value (excl. VAT)")]//following::p[1]').text    
        notice_data.netbudgetlc = float(netbudgetlc.replace(',','').strip())
        notice_data.est_amount = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass 
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of tender procedure")]//following::p[1]').text          
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual )
        notice_data.type_of_procedure = fn.procedure_mapping("assets/cz_nipez_procedure.csv",type_of_procedure)  
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '(//*[contains(text(),"Type")]//following::p[1])[2]').text  
        if 'Public supply contract' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Public Service Contract' in notice_data.contract_type_actual or 'Service concession' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Public works contract' in notice_data.contract_type_actual or 'Works concession' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = page_details.find_element(By.XPATH, '(//*[contains(text(),"Date of publication")]//following::p[1])[1]').text
        publish_date = re.findall('\d+/\d+/\d+, \d+:\d+ [apAP][mM]', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date, '%m/%d/%Y, %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass        

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return        

    try:
        notice_data.class_codes_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Code from the CPV code list")]//following::p[1]').text  
    except Exception as e:
        logging.info("Exception in class_codes_at_source: {}".format(type(e).__name__))
        pass   

    try:
        notice_data.class_title_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Name from the CPV code list")]//following::p[1]').text  
    except Exception as e:
        logging.info("Exception in class_title_at_source: {}".format(type(e).__name__))
        pass    
    
    try:
        cpvs_data = cpvs()
        cpvs_data.cpv_code = notice_data.class_codes_at_source.split('-')[0].strip()        
        notice_data.cpv_at_source = notice_data.class_codes_at_source
        notice_data.class_at_source = 'CPV'
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass
        
    try:
        notice_url_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Contracting authority")]//following::a[1]').get_attribute("href")  
        fn.load_page(page_details2,notice_url_2,80)
        logging.info(notice_url_2)
        time.sleep(7)    
    except Exception as e:
        logging.info("Exception in notice_url_2: {}".format(type(e).__name__))
        pass         

    try:
        Refuse_all_click_on_page_details = WebDriverWait(page_details2, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Refuse all")]')))
        page_details2.execute_script("arguments[0].click();",Refuse_all_click_on_page_details)
        logging.info("Refuse_all_click_on_page_details")            
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")
    except Exception as e:
        logging.info("Exception in Refuse_all_click_on_page_details: {}".format(type(e).__name__))
        pass    
        
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"Phone 1")]//following::p[1])[1]').text  
        customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"E-mail")]//following::p[1])[1]').text  
        try:
            Title_before_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Title before name")]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in Title_before_name: {}".format(type(e).__name__)) 
            pass              
        contact_person_1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Name")]//following::p[1])[2]').text  
        contact_person_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Surname")]//following::p[1]').text  
        try:
            customer_details_data.contact_person = f'{Title_before_name} {contact_person_1} {contact_person_2}'
        except:
            customer_details_data.contact_person = f'{contact_person_1} {contact_person_2}'        
        try:
            customer_details_data.org_website = page_details2.find_element(By.XPATH, '//*[contains(text(),"WWW")]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__)) 
            pass    
        
        try:
            customer_details_data.type_of_authority_code = page_details2.find_element(By.XPATH, '//*[contains(text(),"Contracting authority category")]//following::p[1]').text   
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__)) 
            pass      
        
        customer_details_data.org_country = 'CZ'
        customer_details_data.org_language = 'CS'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass     

    
    try:
        Other_information_click = page_details2.find_element(By.XPATH, '//*[contains(text(),"Other information on the organisation")]').click() 
        time.sleep(3)
        notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")  
    except Exception as e:
        logging.info("Exception in notice_url_4: {}".format(type(e).__name__))
        pass    

    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description of object")]//following::p[1]').text 
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass    
    
    try:
        lot_text = page_details.find_element(By.CSS_SELECTOR, 'div.gov-tabs__content-holder > div > div:nth-child(5) > div > div > table > tbody > tr').text 

        lot_number = 1

        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.gov-tabs__content-holder > div > div:nth-child(5) > div > div > table > tbody > tr'): 
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            try:
                notice_url_3 = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")  
                fn.load_page(page_details3,notice_url_3,80)
                logging.info(notice_url_3)
                time.sleep(7)    
            except Exception as e:
                logging.info("Exception in notice_url_3: {}".format(type(e).__name__))
                pass  

            try:
                Refuse_all_click_on_page_details = WebDriverWait(page_details3, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Refuse all")]')))
                page_details3.execute_script("arguments[0].click();",Refuse_all_click_on_page_details)
                logging.info("Refuse_all_click_on_page_details")            
                notice_data.notice_text += page_details3.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")
            except Exception as e:
                logging.info("Exception in Refuse_all_click_on_page_details: {}".format(type(e).__name__))
                pass     

            try:
                lot_details_data.lot_description = page_details3.find_element(By.XPATH, '//*[contains(text(),"Description of item")]//following::p[1]').text  
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass     

            try:
                lot_quantity = single_record.find_element(By.XPATH, '//*[contains(text(),"Quantity")]//following::p[1]').text
                lot_details_data.lot_quantity = float(lot_quantity)
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_quantity_uom = single_record.find_element(By.XPATH, '//*[contains(text(),"Unit")]//following::p[1]').text 
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass                

            try:
                lot_cpvs_data = lot_cpvs()
                lot_cpvs_data.lot_cpv_code = notice_data.class_codes_at_source.split('-')[0].strip()
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_cpv_at_source = notice_data.class_codes_at_source
            lot_details_data.lot_class_codes_at_source = notice_data.class_codes_at_source     

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    lot_format_text = page_details.find_element(By.CSS_SELECTOR, 'div.gov-tabs__links-holder ').text    
        
    if 'DOCUMENTS' in lot_format_text:        
        try:
            notice_url_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Documents")]').get_attribute("href")  
            fn.load_page(page_details2,notice_url_2,80)
            logging.info(notice_url_2)
            time.sleep(7)    
        except Exception as e:
            logging.info("Exception in notice_url_2: {}".format(type(e).__name__))
            pass   
        
        try:
            Refuse_all_click_on_page_details = WebDriverWait(page_details2, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Refuse all")]')))   
            page_details2.execute_script("arguments[0].click();",Refuse_all_click_on_page_details)
            logging.info("Refuse_all_click_on_page_details")            
            notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in Refuse_all_click_on_page_details: {}".format(type(e).__name__))
            pass  
        
        try:              
            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'table > tbody > tr'):  
                attachments_data = attachments()
                attachments_data.file_name  = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > a').text
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > div > a').get_attribute('href')   
                attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass  

    if 'RESULT' in lot_format_text:        
        try:
            notice_url_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Result")]').get_attribute("href")  
            fn.load_page(page_details2,notice_url_2,80)
            logging.info(notice_url_2)
            time.sleep(7)    
        except Exception as e:
            logging.info("Exception in notice_url_2: {}".format(type(e).__name__))
            pass   
        
        try:
            Refuse_all_click_on_page_details = WebDriverWait(page_details2, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Refuse all")]')))   
            page_details2.execute_script("arguments[0].click();",Refuse_all_click_on_page_details)
            logging.info("Refuse_all_click_on_page_details")            
            notice_data.notice_text += page_details2.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")
        except Exception as e:
            logging.info("Exception in Refuse_all_click_on_page_details: {}".format(type(e).__name__))
            pass 
        
        try:              
            for single_record in page_details2.find_elements(By.CSS_SELECTOR, 'table > tbody > tr > td:nth-child(3) > div'):  
                attachments_data = attachments()
                attachments_data.file_name  = single_record.find_element(By.CSS_SELECTOR, 'a').text
                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')   
                attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass          

    for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.gov-tabs__links-holder > a')[1:]:
        if 'DOCUMENTS' not in single_record.text:
            single_record.click()
            time.sleep(3)
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-content').get_attribute("outerHTML")
    
    
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
arguments= ['ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
page_details2 = fn.init_chrome_driver(arguments) 
page_details3 = fn.init_chrome_driver(arguments) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://nen.nipez.cz/en/verejne-zakazky/p:vz:stavZP=neukoncena","https://nen.nipez.cz/en/verejne-zakazky/p:vz:stavZP=zrusena"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)
                
        try:
            Refuse_all_click = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Refuse all")]')))
            page_main.execute_script("arguments[0].click();",Refuse_all_click)
            logging.info("Refuse_all_click")            
        except Exception as e:
            logging.info("Exception in Refuse_all_click: {}".format(type(e).__name__))
            pass              

        try:
            for page_no in range(1,12):
                page_check = WebDriverWait(page_main, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table > tbody > tr:nth-child(1)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table > tbody > tr')))[records]   
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
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,"//a[contains(@class,'gov-pagination__item gov-pagination__item--arrow-right')]"))) 
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    page_check2 = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table > tbody > tr:nth-child(1)'))).text  
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table > tbody > tr:nth-child(1)'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except Exception as e:
            logging.info('No new record')
            break
            
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    page_details2.quit() 
    page_details3.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)            
            