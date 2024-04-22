from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_qld_ca"
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
SCRIPT_NAME = "au_qld_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'au_qld_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'AUD'
    notice_data.main_language = 'EN'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    
    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > font').text

        if 'Awarded' in document_type_description:

            notice_data.document_type_description = document_type_description

            try:
                notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > b').text 
            except Exception as e:
                logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
                pass

            try:
                notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a:nth-child(1)').text  
                notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
            except:
                try:
                    notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td > u').text  
                    notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
                except Exception as e:
                    logging.info("Exception in local_title: {}".format(type(e).__name__))
                    pass
                
            try:
                publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4) > span.SUMMARY_OPENINGDATE").text  
                notice_data.publish_date = datetime.strptime(publish_date,'%H:%M %p , %d %b, %Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return

            try:
                view_click = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5) > a > img').click()
                time.sleep(5)
            except Exception as e:
                logging.info("Exception in view_click: {}".format(type(e).__name__))
                pass
            
            try:
                view_click_url = page_main.find_element(By.XPATH, '/html/body/div[1]/table/tbody/tr/td/table/tbody/tr/td/a[2]').get_attribute("href")
                time.sleep(5)
            except Exception as e:
                logging.info("Exception in view_click_url: {}".format(type(e).__name__))
                pass

            try:
                notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > a:nth-child(1)').get_attribute("href")                     
                fn.load_page(page_details,notice_data.notice_url,80)
                logging.info(notice_data.notice_url)
                try:
                    notice_data.notice_no = notice_data.notice_url.split('id=')[1].split('&')[0]
                except Exception as e:
                    logging.info("Exception in notice_no: {}".format(type(e).__name__))
                    pass
            except:
                try:
                    notice_data.notice_url = view_click_url

                    try:
                        notice_data.notice_no = notice_data.notice_url.split("=")[-1]
                    except Exception as e:
                        logging.info("Exception in notice_no: {}".format(type(e).__name__))
                        pass
                except Exception as e:
                    logging.info("Exception in notice_url: {}".format(type(e).__name__))
                    notice_data.notice_url = url

            try:
                notice_data.notice_text += page_details.find_element(By.ID, '#main').get_attribute("outerHTML")  

                notice_data.notice_text += tender_html_element.get_attribute("outerHTML")    
            except:
                notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

            try:
                notice_data.notice_url_2 = view_click_url
                fn.load_page(page_details1,notice_data.notice_url_2,80)
                logging.info(notice_data.notice_url)
            except Exception as e:
                logging.info("Exception in notice_url_2: {}".format(type(e).__name__))
                notice_data.notice_url = url

            try:
                notice_data.notice_text += page_details1.find_element(By.ID, '#main').get_attribute("outerHTML")  
            except:
                notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

            if notice_data.notice_url == view_click_url:
                try:
                    notice_data.category = page_details1.find_element(By.XPATH, '//*[contains(text(),"UNSPSC 1")]//following::td[1]').text.split('-')[0].strip()
                    try:
                        cpv_codes = fn.CPV_mapping("assets/au_qld_ca_unspscpv.csv",notice_data.category)
                        for cpv_code in cpv_codes:
                            cpvs_data = cpvs()
                            cpvs_data.cpv_code = cpv_code
                            cpvs_data.cpvs_cleanup()
                            notice_data.cpvs.append(cpvs_data)
                    except Exception as e:
                        logging.info("Exception in category: {}".format(type(e).__name__))
                        pass
                except Exception as e:
                    logging.info("Exception in category: {}".format(type(e).__name__))
                    pass
            else:
                try:
                    category = ''
                    for single_record in page_details.find_elements(By.CSS_SELECTOR, 'tr:nth-child(1) > td:nth-child(2) > table:nth-child(5) > tbody > tr'): 
                        if 'UNSPSC' in single_record.text or 'Mega Category' in single_record.text:

                            test_category = single_record.text.split(':')[1].split('-')[0].strip()
                            category += single_record.text.split(':')[1].split('-')[0].strip()
                            category += ','

                            if 'Mega Category' in single_record.text:
                                cpv_codes = fn.assign_cpvs_from_title(notice_data.notice_title , category = test_category)  
                            else:
                                cpv_codes = fn.CPV_mapping("assets/au_qld_ca_unspscpv.csv",test_category)
                            for cpv_code in cpv_codes:
                                cpvs_data = cpvs()
                                cpvs_data.cpv_code = cpv_code
                                cpvs_data.cpvs_cleanup()
                                notice_data.cpvs.append(cpvs_data)
                    notice_data.category = category.rstrip(',')

                except Exception as e:
                    logging.info("Exception in category: {}".format(type(e).__name__))
                    pass                

            try:
                notice_data.local_description = page_details1.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text  
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass

            try:
                notice_data.notice_summary_english = notice_data.local_description
            except Exception as e:
                logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
                pass                

            try:
                notice_contract_type = page_details1.find_element(By.XPATH, '//*[contains(text(),"Type of Work")]//following::td[1]').text 

                if 'Works' in notice_contract_type:
                    notice_data.notice_contract_type = 'Works'
                elif 'Goods and Services' in notice_contract_type:
                    notice_data.notice_contract_type = 'Supply'

            except Exception as e:
                logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
                pass

            try:
                notice_data.contract_type_actual = page_details1.find_element(By.XPATH, '//*[contains(text(),"Type of Work")]//following::td[1]').text 
            except Exception as e:
                logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
                pass

            try:
                est_amount = page_details1.find_element(By.XPATH, '//*[contains(text(),"Total Value of the Contract")]//following::td[1]').text 
                est_amount = est_amount.split('$')[1].split('(')[0].replace(',','')
                notice_data.est_amount = float(est_amount)
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass
            
            try:
                notice_data.additional_tender_url =  page_details1.find_element(By.XPATH, '//*[contains(text(),"Associated with Tender")]//following::td[1]//a').get_attribute("href")  
            except Exception as e:
                logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
                pass

            try:
                notice_data.grossbudgetlc = notice_data.est_amount
            except Exception as e:
                logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
                pass

            try:
                notice_data.contract_duration = page_details1.find_element(By.XPATH, '//*[contains(text(),"Period Contract")]//following::td[1]').text 
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass   

            try:              

                customer_details_data = customer_details()

                org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'table:nth-child(5) tr td:nth-child(3) > span').text  
                customer_details_data.org_name = org_name.split('Issued by')[1].split('UNSPSC:')[0].strip()
                try:
                    customer_details_data.contact_person = page_details1.find_element(By.XPATH,'(//*[contains(text(),"Contact")])[3]//following::td[1]').text  
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    org_phone = page_details1.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::td[1]').text 
                    customer_details_data.org_phone = org_phone.split('OFFICE:')[1].strip()
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_email = page_details1.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::td[1]').text  
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass                

                customer_details_data.org_country = 'AU'
                customer_details_data.org_language = 'EN'
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)

            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass

            if 'Lot' in notice_data.local_description:
                lot_number = 1
                try:     
                    for single_record in page_details1.find_elements(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]/p'):
                        lot_data = single_record.text
                        if 'Lot' in lot_data:
                            lot_details_data = lot_details()
                            lot_details_data.lot_number = lot_number
                            
                            lot_details_data.lot_actual_number = lot_data.split('.')[0].strip()
                            lot_details_data.lot_title = lot_data.split('.')[1].strip()

                            try:
                                award_text = page_details1.find_element(By.XPATH, '*//*[@summary="displays contractors"]').text
                                award_text_1 =award_text.split(')')

                                for i in award_text_1[1:]:
                                    award_details_data = award_details()
                                    award_details_data.bidder_name = i.split('\n')[0].strip()
                                    award_details_data.address = i.split('\n')[1].split('\n')[0].strip()
                                    award_details_data.grossawardvaluelc = float(i.split('Price: $')[1].split('\n')[0].strip())
                                    award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span:nth-child(11)').text  
                                    award_details_data.award_date = datetime.strptime(award_date,'%H:%M %p , %d %b, %Y').strftime('%Y/%m/%d')
                                    award_details_data.award_details_cleanup()
                                    lot_details_data.award_details.append(award_details_data)

                            except Exception as e:
                                logging.info("Exception in award_details: {}".format(type(e).__name__))
                                pass

                            try:
                                award_text = page_details1.find_element(By.XPATH, '*//*[@summary="displays contractors"]').text.strip()
                                award_text_lines = award_text.split('\n')
                                evaluation_line = award_text_lines[-1]
                                matches = re.findall(r'(\d+%)\s*([a-z A-Z+]+)', evaluation_line)
                                for match in matches:
                                    lot_criteria_data = lot_criteria()
                                    weight, title = match
                                    lot_criteria_data.lot_criteria_title = title
                                    lot_criteria_data.lot_criteria_weight =int(weight.split('%')[0])

                                    lot_criteria_data.lot_criteria_cleanup()
                                    lot_details_data.lot_criteria.append(lot_criteria_data)
                            except Exception as e:
                                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                                pass
                            
                            lot_details_data.lot_contract_type = notice_data.notice_contract_type 
                            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                except Exception as e:
                    logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                    pass
                
            else:
                try:     

                    lot_details_data = lot_details()
                    lot_details_data.lot_number = 1

                    try:
                        lot_details_data.lot_title = notice_data.local_title
                        notice_data.is_lot_default = True
                    except Exception as e:
                        logging.info("Exception in lot_title: {}".format(type(e).__name__))
                        pass

                    try:
                        award_text = page_details1.find_element(By.XPATH, '*//*[@summary="displays contractors"]').text
                        award_text_1 =award_text.split(')')

                        for i in award_text_1[1:]:
                            award_details_data = award_details()
                            award_details_data.bidder_name = i.split('\n')[0].strip()
                            award_details_data.address = i.split('\n')[1].split('\n')[0].strip()
                            award_details_data.grossawardvaluelc = float(i.split('Price: $')[1].split('\n')[0].strip())
                            award_date = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > span:nth-child(11)').text  
                            award_details_data.award_date = datetime.strptime(award_date,'%H:%M %p , %d %b, %Y').strftime('%Y/%m/%d')

                            award_details_data.award_details_cleanup()
                            lot_details_data.award_details.append(award_details_data)

                    except Exception as e:
                        logging.info("Exception in award_details: {}".format(type(e).__name__))
                        pass
   
                    try:
                        award_text = page_details1.find_element(By.XPATH, '*//*[@summary="displays contractors"]').text.strip()
                        award_text_lines = award_text.split('\n')
                        evaluation_line = award_text_lines[-1]

                        matches = re.findall(r'(\d+%)\s*([a-z A-Z+]+)', evaluation_line)
                        for match in matches:
                            lot_criteria_data = lot_criteria()
                            weight, title = match
                            lot_criteria_data.lot_criteria_title = title
                            lot_criteria_data.lot_criteria_weight =int(weight.split('%')[0])
                            lot_criteria_data.lot_criteria_cleanup()
                            lot_details_data.lot_criteria.append(lot_criteria_data)
                    except Exception as e:
                        logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                        pass

                    lot_details_data.lot_contract_type = notice_data.notice_contract_type 
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                            
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                except Exception as e:
                    logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
                    pass
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
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
page_details = fn.init_chrome_driver(arguments)
page_details1 = fn.init_chrome_driver(arguments)
 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://qtenders.epw.qld.gov.au/qtenders/tender/search/tender-search.do?action=advanced-tender-search-awarded-tender&orderBy=closeDate&CSRFNONCE=3915E437651493117E23FAF983855B97"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        sorting_by_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#orderBy'))).click()
        time.sleep(3)
        awarded_date_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#orderBy > option:nth-child(7)'))).click() 
        time.sleep(3)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'(//*[@id="hcontent"]//following::tr[not(@style="display:none")])[5]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="hcontent"]//following::tr[not(@style="display:none")]')))
                length = len(rows)
                
                for records in range(4,length,2):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="hcontent"]//following::tr[not(@style="display:none")]')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'(//*[@id="hcontent"]//following::tr[not(@style="display:none")])[5]'),page_check))
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
