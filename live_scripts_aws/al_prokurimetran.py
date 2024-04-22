from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "al_prokurimetran"
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
SCRIPT_NAME = "al_prokurimetran"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
   
    notice_data.script_name = 'al_prokurimetran'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AL'
    notice_data.performance_country.append(performance_country_data) 
    
    notice_data.currency = 'ALL'
   
    notice_data.main_language = 'SQ'
   
    notice_data.procurement_method = 2  
                                             

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if  'Planning Stage' in notice_type:
            notice_data.notice_type = 3
            notice_data.script_name = 'al_prokurimetran_pp'
        elif 'Cancelled Procurement' in notice_type or 'Re-Proclaimed Procurement' in notice_type or 'Re-Proclaimed and Announced the Winner' in notice_type or 'Re-Proclaimed and Signed the Contract' in notice_type or 'Re-Proclaimed and Signed the Contract + Additional Contract' in notice_type or 'Re-Proclaimed and Cancelled' in notice_type:
            notice_data.notice_type = 16
            notice_data.script_name = 'al_prokurimetran_amd'
        elif "Announced the Winner" in notice_type or 'Signed the Contract + Additional Contract' in notice_type or 'Signed the Contract' in notice_type:
            notice_data.notice_type = 7
            notice_data.script_name = 'al_prokurimetran_ca'
        elif "Announced Procurement" in notice_type:
            notice_data.notice_type = 4
            notice_data.script_name = 'al_prokurimetran_spn'
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
             
    try:
        netbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(3)').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        notice_data.netbudgetlc =float(netbudgetlc.replace(',','').strip())
        notice_data.est_amount  = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        customer_details_data.org_country = 'AL'
        customer_details_data.org_language = 'SQ'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        bidder_name =tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
    except:
        pass
    
    try:
        grossawardvaluelc1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text
    except Exception as e:
        logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
        pass  
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, ' td:nth-child(2) > a').get_attribute("href") 
    except:
        pass
    
    try:                            
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#tabs').get_attribute("outerHTML")                     
        except:
            pass

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender object')]//following::td[1]").text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass 

        try:#	08-03-2024
            publish_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Tender Publication Date')]//following::td[1]").text
            publish_date = re.findall('\d+-\d+-\d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

        if notice_data.publish_date is not None and notice_data.publish_date < threshold:
            return

        try:
            notice_deadline = page_details.find_element(By.XPATH, "//*[contains(text(),'Last date of Submitted Documents')]//following::td[1]").text
            notice_deadline = re.findall('\d+-\d+-\d{4}',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except Exception as e:
            logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
            pass

        try:#06-03-2024
            tender_contract_start_date = page_details.find_element(By.XPATH, "//*[contains(text(),'Contract date')]//following::td[1]").text
            try:
                tender_contract_start_date = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',tender_contract_start_date)[0]
                notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d/%m/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
            except:
                tender_contract_start_date = re.findall('\d+-\d+-\d{4}',tender_contract_start_date)[0]
                notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d-%m-%Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'Reference No.')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Procurement Method')]//following::td[1]").text
            notice_data.type_of_procedure = fn.procedure_mapping("assets/al_prokurimetran_ca_procedure.csv",notice_data.type_of_procedure_actual)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:
            notice_data.contract_duration = page_details.find_element(By.XPATH, "//*[contains(text(),'Planned Milestones of Contract / Start and End Date')]//following::td[1]").text
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

        try:   
            for single_record in page_details.find_elements(By.XPATH, "(//*[contains(text(),'Public Announcement Bulletin')]//following::td[1])[1]/table/tbody/tr/td/a"):
                attachments_data = attachments()

                attachments_data.file_name = single_record.text

                attachments_data.external_url = single_record.get_attribute("href")

                try:
                    attachments_data.file_type = attachments_data.external_url.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                if attachments_data.external_url != '':
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        try:
            if notice_data.notice_type == 7:
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1

                lot_details_data.lot_title = notice_data.local_title
                notice_data.is_lot_default = True
                lot_details_data.lot_title_english=notice_data.notice_title

                award_details_data = award_details()
                award_details_data.bidder_name =bidder_name

                try:
                    award_details_data.contract_duration = notice_data.contract_duration
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

                try:
                    grossawardvaluelc = grossawardvaluelc1
                    grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                    award_details_data.grossawardvaluelc =float(grossawardvaluelc.replace(',','').strip())
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass

                try:#11-03-2024
                    award_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Bidder Announcement date")]//following::td[1]').text
                    award_date = re.findall('\d+-\d+-\d{4}',award_date)[0]
                    award_details_data.award_date = datetime.strptime(award_date,'%d-%m-%Y').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
                    pass

                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)

                if lot_details_data.award_details != []:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data) 
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass   

    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
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
    urls = ["https://prokurimetransparente.al/en/tender/list/status_id/1?"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(5)

        lst = [81,4,5,6,7,71,8,2,31,3,1]
        for no in lst:
            nums = str(no)
            Stage_Procedure = Select(page_main.find_element(By.XPATH,'//*[@id="tender_status"]'))
            Stage_Procedure.select_by_value(nums)
            time.sleep(2)
            
            click_search = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#submit_btn')))
            page_main.execute_script("arguments[0].click();",click_search)
            time.sleep(5)

            try:
                for page_no in range(2,8):                                                                
                    page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#results_table > tbody > tr'))).text
                    rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#results_table > tbody > tr')))
                    length = len(rows)
                    for records in range(0,length):
                        tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#results_table > tbody > tr')))[records]
                        extract_and_save_notice(tender_html_element)
                        if notice_count >= MAX_NOTICES:
                            break

                    try:   
                        next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                        page_main.execute_script("arguments[0].click();",next_page)
                        logging.info("Next page")
                        time.sleep(2)
                        WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#results_table > tbody > tr'),page_check))
                    except Exception as e:
                        logging.info("Exception in next_page: {}".format(type(e).__name__))
                        logging.info("No next page")
                        break
            except:
                logging.info("No new record")
                pass
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
