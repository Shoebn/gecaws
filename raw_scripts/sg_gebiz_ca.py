# Login credentials:
# Id:Z4781100
# Password:dgMarket@2024


# Follow the steps to find data.
# 1)After opening the main url click on "#listButton2_MAIN-DIV" button.Then click on "For Foreigners w/o Singpass" option in dropdown."
# 2)Then in "GeBIZ ID" and "Password" field Enter the given Id and Password. and Click on Submit button.
# 3)Then select "dgMarket International Inc" option.Then click on Next.
# 4)Then click "div.headerMenu2_MENU-BUTTON-LOGIN > div:nth-child(2)"=Opportunities tab
# 5)Then click on "div.nav.nav-tabs.formTabBar_TAB-BAR > div:nth-child(2)"=Closed tab
# 6)Then click on "contentForm:j_idt908_commandLink-SPAN"=Awarded	tab
# 7)Then click on "//*[contains(text(),"Sort by")]//following::div[1]" dropdown button. and select "Published Date (Latest First)" option.



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
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "sg_gebiz_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'sg_gebiz_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'SG'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'SGD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Quotation
    # Onsite Comment -1.split notice_no.Here "Quotation - RGS000ETQ24000003 / PR2024-0148" grab "RGS000ETQ24000003" no in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > div.formSectionHeader6_TEXT').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Quotation
    # Onsite Comment -1.split notice_no.Here "Quotation - RGS000ETQ24000003 / PR2024-0148" grab "PR2024-0148" no in related_tender_id.

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > div.formSectionHeader6_TEXT').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    # Onsite Field -Quotation
    # Onsite Comment -1.split notice_no.Here "Quotation - RGS000ETQ24000003 / PR2024-0148" grab "Quotation" no in document_type_description.

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div > div.formSectionHeader6_TEXT').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(3) > div > div > div > div:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type.Here "Transportation ⇒ Bus Hire" grab only "Bus Hire"       2."sg_gebiz_ca_contracttype.csv" map this file to this field.

    try:
        notice_data.notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_contract_type.Here "Transportation ⇒ Bus Hire" grab only "Bus Hire"

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split category.Here "Transportation ⇒ Bus Hire" grab only "Bus Hire"
    try:
        notice_data.category = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)").text
        cpv_codes = fn.CPV_mapping("assets/sg_gebiz_ca_procedure.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(1) > div > div > div > div > div > span > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    # Onsite Field -None
    # Onsite Comment -1)add test from "nav-item formTabBar_TAB-BAR-OUTER-DIV" this tabs from page_main in notice_text. 			2)add "#contentForm\:j_idt915 > div > div > div > div" this also in notice_text from tender_html_element.
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#contentForm').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    



# Onsite Field -QUOTATION DOCUMENTS
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"QUOTATION DOCUMENTS")]//following::div[4]'):
            attachments_data = attachments()
            attachments_data.file_name = 'Tender_documents'
        # Onsite Field -None
        # Onsite Comment -None

            attachments_data.external_url = page_main.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt402\:j_idt427 > div > div > div > div > div > input').get_attribute('href')
            
        
        # Onsite Field -None
        # Onsite Comment -1)split file_type from external_url.

            try:
                attachments_data.file_type = page_main.find_element(By.CSS_SELECTOR, '#contentForm\:j_idt402\:j_idt427 > div > div > div > div > div > input').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -AWARDING AGENCY
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.XPATH, '//*[contains(text(),"AWARDING AGENCY")]//following::div[1]'):
            customer_details_data = customer_details()
            customer_details_data.org_country = 'SG'
            customer_details_data.org_language = 'EN'
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(3) > div > div > div > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.contact_person = page_main.find_element(By.XPATH, '''//*[contains(text(),"CONTACT PERSON'S DETAILS")]//following::div[1]''').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1)split the data after "CONTACT PERSON'S DETAILS".	2)grab only 2nd line in org_email.

            try:
                customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"AWARDING AGENCY")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1)split the data after "CONTACT PERSON'S DETAILS".	2)grab only 3rd line in org_phone.

            try:
                customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"AWARDING AGENCY")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1)split the data after "CONTACT PERSON'S DETAILS".	2)grab only 5th line in org_address.

            try:
                customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"AWARDING AGENCY")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    




                                                                # To grab all the below data click on "Award" tab in page_main

# Onsite Field -Here multiple lots can be present.So grab all the lot_details data.
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#contentForm\:j_idt233 > div'):
            lot_details_data = lot_details()
        # Onsite Field -None
        # Onsite Comment -1.split after "Item No.".	grab like eg.,"Item No. 3"

            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.XPATH, '//*[contains(text(),"Awarded Items")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.split between "Item No." and "Unit of Measurement".

            try:
                lot_details_data.lot_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Awarded Items")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Awarded Items >> Unit of Measurement
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_main.find_element(By.XPATH, '//*[contains(text(),"Unit of Measurement")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Awarded Items >> Quantity
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_main.find_element(By.XPATH, '//*[contains(text(),"Quantity")]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass

        # Onsite Field -
        # Onsite Comment -1.split notice_contract_type.Here "Transportation ⇒ Bus Hire" grab only "Bus Hire"       2."sg_gebiz_ca_contracttype.csv" map this file to this field.

            try:
                lot_details_data.contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -
        # Onsite Comment -1.split notice_contract_type.Here "Transportation ⇒ Bus Hire" grab only "Bus Hire"

            try:
                lot_details_data.lot_contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-7.formColumn_MAIN.formColumns_COLUMN-TD > div > div:nth-child(4) > div > div > div > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None

            try:
                for single_record in page_main.find_elements(By.XPATH, '#contentForm\:j_idt233 > div'):
                    award_details_data = award_details()
		
                    # Onsite Field - Awarded to >> Awarded Items
                    # Onsite Comment -None

                    award_details_data.bidder_name = page_main.find_element(By.XPATH, '//*[contains(text(),"Awarded to")]//following::div[1]').text
			
                    # Onsite Field -Awarded Items >> Awarded Value
                    # Onsite Comment -1.split after "Awarded Value".

                    award_details_data.grossawardvaluelc = page_main.find_element(By.XPATH, '//*[contains(text(),"Awarded to")]//following::div[7]').text
			
                    # Onsite Field -Awarding Agency >> Awarded Date
                    # Onsite Comment -None

                    award_details_data.award_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Awarded Date")]//following::div[1]').text
			
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
    
    # Onsite Field -Awarding Agency >> Total Awarded Value
    # Onsite Comment -None

    try:
        notice_data.est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Total Awarded Value")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Awarding Agency >> Total Awarded Value
    # Onsite Comment -None

    try:
        notice_data.grossbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Total Awarded Value")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title)
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
    urls = ["https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,15):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/form[2]/div[7]/div/div/div[1]/div/div/div/div/div[2]/div/div[6]/div/div/div/div'),page_check))
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
