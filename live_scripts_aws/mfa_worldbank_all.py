from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "mfa_worldbank_all"
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
SCRIPT_NAME = "mfa_worldbank_all"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'mfa_worldbank_all'
    notice_data.procurement_method = 2


    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        performance_country_data = performance_country()
        performance_country_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        if 'West Bank and Gaza' in performance_country_1 or 'OECS Countries' in performance_country_1 or 'Andean Countries' in performance_country_1 or 'Western and Central Africa' in performance_country_1 or 'Eastern and Southern Africa' in performance_country_1 or 'Pacific Islands' in performance_country_1 or 'World,Middle East and North Africa' in performance_country_1 or 'Latin America' in performance_country_1 or 'Latin America and Caribbean' in performance_country_1 or 'Multi-Regional' in performance_country_1 or 'Africa,Western Africa' in performance_country_1 or 'Eastern Africa' in performance_country_1 or 'Europe and Central Asia' in performance_country_1 or 'South East Asia' in performance_country_1 or 'East Asia and Pacific' in performance_country_1 or 'South Asia' in performance_country_1:  
            performance_country_data.performance_country = 'US'
            notice_data.performance_country.append(performance_country_data)
            
        elif 'Kyrgyz Republic' in performance_country_1:
            performance_country_data.performance_country = 'KG'
            notice_data.performance_country.append(performance_country_data)
        
        else:
            performance_country_data.performance_country = fn.procedure_mapping("assets/mfa_worldbank_all_countrycode.csv",performance_country_1)  
            notice_data.performance_country.append(performance_country_data)

    except Exception as e:
        logging.info("Exception in performance_country: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.project_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
    except Exception as e:
        logging.info("Exception in project_name: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
        if 'Bids' in notice_type:
            notice_data.notice_type = 4
        elif 'Goods and Works Award' in notice_type:
            notice_data.notice_type = 4
        elif 'Small Contracts Award' in notice_type:
            notice_data.notice_type = 4
        elif 'Consultant Award' in notice_type:
            notice_data.notice_type = 4
        elif 'Request for Expression of Interest' in notice_type:
            notice_data.notice_type = 5
        elif 'Contract Award' in notice_type:
            notice_data.notice_type = 7
        elif 'General Procurement Notice' in notice_type:
            notice_data.notice_type = 2
        elif 'Invitation for Prequalification' in notice_type:
            notice_data.notice_type = 6
    except Exception as e:
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass

    try:
        main_language_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
        notice_data.main_language = fn.procedure_mapping("assets/mfa_worldbank_all_languagecode.csv",main_language_1) 
    except:
        pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
        notice_data.publish_date = datetime.strptime(publish_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1) > a').get_attribute("href")   
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.project_par.parsys').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice No")]//following::p[1]').text 
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Borrower Bid Reference")]//following::p[1]').text  
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Submission Deadline Date/Time")]//following::p[1]').text 
        if notice_data.notice_type != 7:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = '1012'
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    if notice_data.notice_type != 7:
        try:              
            customer_details_data = customer_details()

            org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Organization/Department")]//following::p[1]').text  
            if len(org_name)>5:
                customer_details_data.org_name = org_name
            else:
                customer_details_data.org_name = 'The World Bank'
                customer_details_data.org_parent_id = 1012

            try:
                org_country = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                if 'West Bank and Gaza' in performance_country_1 or 'OECS Countries' in performance_country_1 or 'Andean Countries' in performance_country_1 or 'Western and Central Africa' in performance_country_1 or 'Eastern and Southern Africa' in performance_country_1 or 'Pacific Islands' in performance_country_1 or 'World,Middle East and North Africa' in performance_country_1 or 'Latin America' in performance_country_1 or 'Latin America and Caribbean' in performance_country_1 or 'Multi-Regional' in performance_country_1 or 'Africa,Western Africa' in performance_country_1 or 'Eastern Africa' in performance_country_1 or 'Europe and Central Asia' in performance_country_1 or 'South East Asia' in performance_country_1 or 'East Asia and Pacific' in performance_country_1 or 'South Asia' in performance_country_1:  
                    customer_details_data.org_country = 'US'
                    
                elif 'Kyrgyz Republic' in performance_country_1:
                    customer_details_data.org_country = 'KG'      
                    
                else:
                    customer_details_data.org_country = fn.procedure_mapping("assets/mfa_worldbank_all_countrycode.csv",performance_country_1) 
            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_language = fn.procedure_mapping("assets/mfa_worldbank_all_languagecode.csv",main_language_1)
            except Exception as e:
                logging.info("Exception in org_language: {}".format(type(e).__name__))
                pass

            try:
                contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"CONTACT INFORMATION")]//following::p[2]').text 
                if len(contact_person)>5:
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            try:
                org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::p[1]').text 
                if len(org_address)>5:
                    customer_details_data.org_address = org_address
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"City")]//following::p[1]').text 
                if len(org_city)>5:
                    customer_details_data.org_city = org_city
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal Code")]//following::p[1]').text 
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

            try:
                org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::p[1]').text  
                if len(org_phone)>5:
                    customer_details_data.org_phone = org_phone
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"CONTACT INFORMATION")]//following::p[9]').text 
                if len(org_email)>5:
                    customer_details_data.org_email = org_email
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Website")]//following::p[1]').text 
                if len(org_website)>5:
                    customer_details_data.org_website = org_website
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:              
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > table:nth-child(9) > tbody > tr')[1:]:
                lot_details_data = lot_details()

                lot_details_data.lot_number = lot_number

                try:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text 
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    else:
        try:
            notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Scope of Contract: ")]//following::span[1]').text  
            if len(notice_summary_english)>5:
                notice_data.notice_summary_english = notice_summary_english
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

        try:
            local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Scope of Contract: ")]//following::span[1]').text   
            if len(local_description)>5:
                notice_data.local_description = local_description
        except Exception as e:  
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:              
            customer_details_data = customer_details()

            try:
                if 'West Bank and Gaza' in performance_country_1 or 'OECS Countries' in performance_country_1 or 'Andean Countries' in performance_country_1 or 'Western and Central Africa' in performance_country_1 or 'Eastern and Southern Africa' in performance_country_1 or 'Pacific Islands' in performance_country_1 or 'World,Middle East and North Africa' in performance_country_1 or 'Latin America' in performance_country_1 or 'Latin America and Caribbean' in performance_country_1 or 'Multi-Regional' in performance_country_1 or 'Africa,Western Africa' in performance_country_1 or 'Eastern Africa' in performance_country_1 or 'Europe and Central Asia' in performance_country_1 or 'South East Asia' in performance_country_1 or 'East Asia and Pacific' in performance_country_1 or 'South Asia' in performance_country_1:  
                    customer_details_data.org_country = 'US'
                
                elif 'Kyrgyz Republic' in performance_country_1:
                    customer_details_data.org_country = 'KG'
                else:
                    customer_details_data.org_country = fn.procedure_mapping("assets/mfa_worldbank_all_countrycode.csv",performance_country_1) 

            except Exception as e:
                logging.info("Exception in org_country: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_language = fn.procedure_mapping("assets/mfa_worldbank_all_languagecode.csv",main_language_1)
            except Exception as e:
                logging.info("Exception in org_language: {}".format(type(e).__name__))
                pass

            customer_details_data.org_name = 'The World Bank'
            customer_details_data.org_parent_id = '1012'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            currency = page_details.find_element(By.XPATH, '(//div[@class="col-sm-6"])[3]').text  
            currency = currency.split('Final Evaluation Price\n')[1].split('\n')[0].strip()
            notice_data.currency = currency[:3].strip()
        except Exception as e:
            try:
                currency = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(4)').text  
                notice_data.currency = currency.split('Signed Contract price\n')[1].split(' ')[0].strip()
            except Exception as e:
                logging.info("Exception in currency: {}".format(type(e).__name__))
                pass

        try:              
            lot_details_data = lot_details()

            lot_details_data.lot_number = 1
            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True

            try:
                award_details_data = award_details()
                
                award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Firm(s):")]//following::b[1]').text

                if 'West Bank and Gaza' in performance_country_1 or 'OECS Countries' in performance_country_1 or 'Andean Countries' in performance_country_1 or 'Western and Central Africa' in performance_country_1 or 'Eastern and Southern Africa' in performance_country_1 or 'Pacific Islands' in performance_country_1 or 'World,Middle East and North Africa' in performance_country_1 or 'Latin America' in performance_country_1 or 'Latin America and Caribbean' in performance_country_1 or 'Multi-Regional' in performance_country_1 or 'Africa,Western Africa' in performance_country_1 or 'Eastern Africa' in performance_country_1 or 'Europe and Central Asia' in performance_country_1 or 'South East Asia' in performance_country_1 or 'East Asia and Pacific' in performance_country_1 or 'South Asia' in performance_country_1:  
                    award_details_data.bidder_country = 'US'

                elif 'Kyrgyz Republic' in performance_country_1:
                    award_details_data.bidder_country = 'KG'
                else:
                    award_details_data.bidder_country = fn.procedure_mapping("assets/mfa_worldbank_all_countrycode.csv",performance_country_1) 

                try:
                    award_date = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(1)').text
                    award_date = award_date.split(')\n')[1]
                    award_details_data.award_date = datetime.strptime(award_date,'%Y/%m/%d').strftime('%Y/%m/%d')
                except Exception as e:
                    logging.info("Exception in award_date: {}".format(type(e).__name__))
                    pass

                try:
                    contract_duration = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(2)').text
                    award_details_data.contract_duration = contract_duration.split('Duration of Contract\n')[1].strip()
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

                try:
                    final_estimated_value = page_details.find_element(By.XPATH, '(//div[@class="col-sm-6"])[3]').text                
                    final_estimated_value = final_estimated_value.split('Final Evaluation Price\n')[1].split('\n')[0].strip()
                    award_details_data.final_estimated_value = float(final_estimated_value[3:].strip())
                except Exception as e:
                    logging.info("Exception in currency: {}".format(type(e).__name__))
                    pass

                try:
                    grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div.row.col-sm-12 > div:nth-child(4)').text
                    grossawardvaluelc = grossawardvaluelc.split('Signed Contract Price\n')[1].split('\n')[0].strip()
                    award_details_data.grossawardvaluelc = float(grossawardvaluelc[3:].strip())
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)
            except:
                try:
                    award_details_data = award_details()

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Awarded Bidder(s):")]//following::b[1]').text  

                    if 'West Bank and Gaza' in performance_country_1 or 'OECS Countries' in performance_country_1 or 'Andean Countries' in performance_country_1 or 'Western and Central Africa' in performance_country_1 or 'Eastern and Southern Africa' in performance_country_1 or 'Pacific Islands' in performance_country_1 or 'World,Middle East and North Africa' in performance_country_1 or 'Latin America' in performance_country_1 or 'Latin America and Caribbean' in performance_country_1 or 'Multi-Regional' in performance_country_1 or 'Africa,Western Africa' in performance_country_1 or 'Eastern Africa' in performance_country_1 or 'Europe and Central Asia' in performance_country_1 or 'South East Asia' in performance_country_1 or 'East Asia and Pacific' in performance_country_1 or 'South Asia' in performance_country_1:  
                        award_details_data.bidder_country = 'US'

                    elif 'Kyrgyz Republic' in performance_country_1:
                        award_details_data.bidder_country = 'KG'
                    else:
                        award_details_data.bidder_country = fn.procedure_mapping("assets/mfa_worldbank_all_countrycode.csv",performance_country_1) 

                    address = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(1) > div').text
                    award_details_data.address = address.split('Country')[0].strip()

                    award_date = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(1)').text  
                    award_date = award_date.split('(YYYY/MM/DD)')[1].strip()
                    award_details_data.award_date = datetime.strptime(award_date,'%Y/%m/%d').strftime('%Y/%m/%d')

                    contract_duration = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(2) > div:nth-child(2)').text  
                    award_details_data.contract_duration = contract_duration.split('Duration of Contract')[1].strip()

                    final_estimated_value = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(2)').text  
                    
                    final_estimated_value = final_estimated_value.split('Evaluated Bid Price')[1].strip()
                    award_details_data.final_estimated_value = float(final_estimated_value[3:].strip())

                    grossawardvaluelc = page_details.find_element(By.CSS_SELECTOR, 'div.col-md-8.col-xs-12 > div > section > div > div:nth-child(5) > div.row.col-sm-12 > div:nth-child(4)').text  
                    grossawardvaluelc = grossawardvaluelc.split('Signed Contract price')[1].strip()
                    award_details_data.grossawardvaluelc = final_estimated_value = float(grossawardvaluelc[3:].strip())
                    
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://projects.worldbank.org/en/projects-operations/procurement?srce=both"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,12):
                page_check = WebDriverWait(page_main, 150).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 150).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div > ul > li:nth-child(13) > a > i')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 150).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div[3]/div[2]/div[2]/div[2]/procurement-search/div/div/div/div/div[1]/div/section/tabset/section/div/projects-tab[1]/table-api/div[1]/div/div[1]/div[2]/div/table/tbody/tr'),page_check))
                except Exception as e:
                    logging.info("Exception in next_page: {}".format(type(e).__name__))
                    logging.info("No next page")
                    break
        except:
            logging.info("No new record")
            break
            
    logging.info("Finished processing. Scraped {} notices".format(notice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)
