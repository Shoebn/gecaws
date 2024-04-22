from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "jm_gojep_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from deep_translator import GoogleTranslator

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "jm_gojep_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'jm_gojep_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'JM'
    notice_data.performance_country.append(performance_country_data)
   
    notice_data.currency = 'JMD'
    
    notice_data.main_language = 'EN'
    
    notice_data.notice_type = 4
    
    notice_data.procurement_method = 2
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
        notice_data.notice_title = GoogleTranslator(source='es', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(10)').text
        publish_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try: 
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR,"td:nth-child(6)").text
        if 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Goods' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass

    try:  
        attachments_data = attachments()
        attachments_data.external_url =  tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(9) > a").get_attribute('href')
        attachments_data.file_name = "Tender Document"
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        fn.load_page(page_details,notice_data.notice_url,80) 
        try:
            notice_data.local_description = page_details.find_element(By.XPATH,'''//*[contains(text(),"Description")]//following::dd[1]''').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Competition unique ID")]//following::dd[1]').text
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
    
        try:
            source_of_funds = page_details.find_element(By.XPATH, '//*[contains(text(),"Funding Source")]//following::dd[1]').text
            if 'Government of Jamaica' in source_of_funds:
                notice_data.source_of_funds = 'Government funded'    
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        try: 
            document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Bid opening date")]//following::dd[1]').text
            document_opening_time = re.findall('\d+/\d+/\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d/%m/%Y').strftime('%Y-%m-%d')
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
    
    
        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Lot Name")]//following::dd[1]'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = single_record.text            
                lot_details_data.lot_title_english = lot_details_data.lot_title                   
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

        try:  
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Common Procurement Vocabulary")]//following::dd[1]').text
            cpv_regex = re.compile(r'\d{8}')
            cpv_code_list = cpv_regex.findall(cpv_code)
            for cpv in cpv_code_list:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass
    
        try:
            notice_data.class_at_source = 'CPV'
            class_codes_at_source = ''
            codes_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Common Procurement Vocabulary")]//following::dd[1]').text
            cpv_regex = re.compile(r'\d{8}')
            code_list = cpv_regex.findall(codes_at_source)
            for codes in code_list:
                class_codes_at_source += codes
                class_codes_at_source += ','
            notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass

        try:
            class_title_at_source = '' 
            single_record = page_details.find_element(By.XPATH, '//*[contains(text(),"Common Procurement Vocabulary")]//following::dd[1]').text.split('\n')
            for record in single_record:
                titles_at_source = re.split("\d{8}.", record)[1]
                class_title_at_source += titles_at_source
                class_title_at_source +=','
            notice_data.class_title_at_source = class_title_at_source.rstrip(',') 
        except Exception as e:
            logging.info("Exception in class_title_at_source: {}".format(type(e).__name__)) 
            pass
        try:
            procurement_method = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Method")]//following::dd[1]').text
            if "Open - NCB" in procurement_method:
                notice_data.procurement_method = 0
            elif "Open - ICB" in procurement_method:
                notice_data.procurement_method = 1
            else:
                notice_data.procurement_method = 2
        except Exception as e:
            logging.info("Exception in procurement_method: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_text += page_details.find_element(By.XPATH,'/html/body/div[1]/div[5]/div[2]/dl').get_attribute('outerHTML')
        except:
            pass

    except:
        pass

    try:
        notice_url1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name of procuring entity")]//following::dd[1]/a').get_attribute("href")                     
    except Exception as e:
        logging.info("Exception in notice_url1: {}".format(type(e).__name__))

    try:     
        fn.load_page(page_details1,notice_url1,80) 
        try:
            notice_data.notice_text += page_details1.find_element(By.XPATH,'/html/body/div[1]/div[5]/div[2]/dl').get_attribute('outerHTML')
        except:
            pass

        try:
            customer_details_data = customer_details()  
            customer_details_data.org_name = page_details1.find_element(By.XPATH, '//*[contains(text(),"Organisation Name")]//following::dd[1]').text
            try:
                customer_details_data.org_address = page_details1.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass 
                
            try:
                customer_details_data.postal_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"Postal Code")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass 
    
            try:
                customer_details_data.org_city = page_details1.find_element(By.XPATH, '//*[contains(text(),"City")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass 
    
            try:
                customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"Email")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
    
            try:
                customer_details_data.org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Phone Number")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
    
            try:
                customer_details_data.org_fax = page_details1.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
    
            try:
                customer_details_data.org_website = page_details1.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass
                
            customer_details_data.org_country = 'JM'
            customer_details_data.org_language = 'EN'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    except:
        pass

    try:  
        attachment_no = notice_data.notice_url.split('resourceId=')[1].strip()
        attachments_data = attachments()
        attachments_data.external_url = 'https://www.gojep.gov.jm/epps/cft/listContractDocuments.do?resourceId='+str(attachment_no)
        attachments_data.file_name = "Tender Documents"
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.gojep.gov.jm/epps/prepareCurrentOpportunities.do?selectedItem=prepareCurrentOpportunities.do"] 
    for url in urls:
        fn.load_page(page_main, url, 120)
        logging.info('----------------------------------')
        logging.info(url)

        try:   
            attachments_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#T01 > thead > tr > th.extra > a')))
            page_main.execute_script("arguments[0].click();",attachments_click)
            time.sleep(3)
        except:
            pass

        try:   
            status_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#sh_T01_8')))
            page_main.execute_script("arguments[0].click();",status_click)
            time.sleep(3)
        except:
            pass

        try:   
            notice_pdf_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#sh_T01_9')))
            page_main.execute_script("arguments[0].click();",notice_pdf_click)
            time.sleep(3)
        except:
            pass

        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#T01 > tbody > tr'))).text
                rows = WebDriverWait(page_main, 120).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#T01 > tbody > tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 200).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#T01 > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#CFTResults > div.Pagination > p:nth-child(2) > button:nth-child(5)')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#T01 > tbody > tr'),page_check))
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
