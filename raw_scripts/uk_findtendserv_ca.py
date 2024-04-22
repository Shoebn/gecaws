from gec_common.gecclass import *
import logging
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
import functions as fn
from functions import ET
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "uk_findtenserv_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'uk_findtenserv_ca'
    
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'UK'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'GBP'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > dd').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.search-result-header').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass     

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")  
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:         
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Short description")]//following::p').text  
    except Exception as e:
        notice_data.notice_summary_english = page_details.find_element(By.CSS_SELECTOR,'#main-content > div:nth-child(3) > p:nth-child(11)').text 
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Short description")]//following::p').text 
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
        
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.govuk-grid-column-three-quarters> p:nth-child(4)").text 
        publish_date = re.findall('\d+ \w+ \d{4}, \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
        
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.govuk-width-container > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        lot_deatils = page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text.split('II.2) Description')
        lot_number = 1
        for lot in lot_deatils[1:]:

            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            try:
                lot_title = lot.split("Title")[1].split('\n')[1].split('\n')[0]
                lot_details_data.lot_title = str(lot_title)
            except:
                lot_details_data.lot_title = notice_data.notice_title
            try:
                lot_details_data.lot_description = lot.split('Description of the procurement\n')[1].split('\n')[0]
            except Exception as e:
                lot_details_data.lot_description = notice_data.local_description
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

            try:
                lot_grossbudget_lc = lot.split('Estimated value\n')[1].split('\n')[0]
                lot_grossbudget_lc = lot_grossbudget_lc.split('VAT:')[1]
                lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())

            except:
                try:
                    lot_grossbudget_lc = page_details.find_element(By.XPATH,'//*[contains(text(),"II.1.7) Total value of the procurement (excluding VAT)")]//following::p[1]').text  
                    lot_grossbudget_lc = lot_grossbudget_lc.split('£')[1].strip()
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
                except:
                    
                    try:
                        lot_grossbudget_lc = notice_data.grossbudgetlc
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace('.','').replace(',','.').strip())
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass

            try:
                lot_details_data.lot_nuts = lot.split('NUTS codes\n')[1].split('\n')[0] 
            except:
                try:
                    lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code")]//following::p[1]').text 
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

            try:
                lot_details_data.contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p[1]').text 
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass


            try:
                lot_details_data.contract_duration = lot.split('Duration in months\n')[1].split('\n')[0] 
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

            try:
                cpv_regex = re.compile(r'\d{8}')
                lot_cpvs_dataa = cpv_regex.findall(lot)
                for cpv in lot_cpvs_dataa:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = cpv
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                pass
            
            try:
                lot_criteria_data = lot_criteria()
                lot_criteria_data.lot_criteria_title = lot.split('Award criteria\n')[1].split('\n')[0] 
                try:
                    lot_criteria_weight = lot_criteria_data.lot_criteria_title.split('Weighting:')[1].strip()
                    if '%' in lot_criteria_weight:
                        lot_criteria_weight = lot_criteria_weight.split('%')[0].strip()
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                    else:
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                except:
                    pass  
                lot_criteria_data.lot_criteria_cleanup()
                lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria_data: {}".format(type(e).__name__))
                pass    

            try:
                award_details_data = award_details()
                award_details_data.bidder_name = page_details.find_element(By.XPATH,'//*[contains(text(),"Name and address of the contractor")]//following::p[1]').text
                try:
                    address_1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[1]').text 
                    address_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[2]').text 
                    address_3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[3]').text  
                    address_4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[4]').text 
                    award_details_data.address = f"{address_1} {address_2} {address_3} {address_4}"

                except Exception as e:
                    logging.info("Exception in address: {}".format(type(e).__name__))
                    pass

                initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Initial estimated total value of the contract/lot:")]').text 
                initial_estimated_value = initial_estimated_value.split('£')[1].strip()
                award_details_data.initial_estimated_value = float(initial_estimated_value.replace('.','').replace(',','.').strip())            

                try:
                    grossawardvalueeuro = page_details.find_element(By.XPATH,'//*[contains(text(),"Total value of the contract/lot:")]').text
                    grossawardvalueeuro = grossawardvalueeuro.split('£')[1].strip()
                    award_details_data.grossawardvalueeuro = float(grossawardvalueeuro.replace('.','').replace(',','.').strip())
                    award_details_data.grossawardvaluelc = award_details_data.grossawardvalueeuro
                except Exception as e:
                    pass
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
            
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except Exception as e:
        logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
        pass            

    try:
        notice_no = page_details.find_element(By.CSS_SELECTOR, 'div.govuk-grid-column-three-quarters> p:nth-child(3)').text
        notice_data.notice_no = notice_no.split('Notice reference:')[1]     
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of procedure")]//following::p[1]').text  
        notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_findtenserv_procedure.csv",notice_data.type_of_procedure_actual) 
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p').text 
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > dd').text 
        try:
            grossbudgetlc = grossbudgetlc.split('£')[1].strip()
        except:
            grossbudgetlc = grossbudgetlc.split('EUR')[0].strip()
        notice_data.grossbudgetlc = float(grossbudgetlc.replace(',','').strip())
        notice_data.est_amount = notice_data.grossbudgetlc
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()

        try:
            customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[1]').text   
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            pass

        try:
            org_address_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[2]').text
            org_address_3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[3]').text
            org_address_4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[4]').text
            customer_details_data.org_address = f"{org_address_2} {org_address_3} {org_address_4}"
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//h4[text()="Email"]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::p[1]').text  
            if len(contact_person)<23:
                customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::p[1]').text 
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code")]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address")]//following::p[1]').text                 
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
      
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    
    try:
        cpvs_data = cpvs()
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text 
        cpvs_data.cpv_code = cpv_code.split('-')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass    

    try:              
        attachments_data = attachments()
        external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Download")]//following::a[1]').click()
        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Download")]//following::a[1]').get_attribute('href') 
        attachments_data.file_name = 'Download'
        if 'PDF' in attachments_data.external_url:
            attachments_data.file_type = 'PDF'
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    urls = ["https://www.find-tender.service.gov.uk/Search/Results"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        
        click_1 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="stage[4]_label"]')))
        page_main.execute_script("arguments[0].click();",click_1)           

        click_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="stage[1]_label"]')))
        page_main.execute_script("arguments[0].click();",click_2)      


        click_3 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="stage[2]_label"]')))
        page_main.execute_script("arguments[0].click();",click_3)      

        click_4 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="adv_search_button"]')))
        page_main.execute_script("arguments[0].click();",click_4) 

        page_main.refresh()
        
        for page_no in range(1,8):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div[1]'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))
            length = len(rows)
        
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
                
                if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                    logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                    break

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                break

            try:   
                next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'a.standard-paginate-next.govuk-link.break-word')))
                page_main.execute_script("arguments[0].click();",next_page)
                logging.info("Next page")
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div[1]'),page_check))
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
    
    
