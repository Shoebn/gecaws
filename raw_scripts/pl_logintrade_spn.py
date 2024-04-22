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
SCRIPT_NAME = "pl_logintrade_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'pl_logintrade_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'PLN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'PL'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.blue-header').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -Notice_no teke from notice_url..........Note:notice_no:"https://ciech.logintrade.net/zapytania_email,1547951,a4566fcd82fc69bfb58790efc2744d78.html" here take "a4566fcd82fc69bfb58790efc2744d78" in notice_no.

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.label').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data publikacji:
    # Onsite Comment -Note:Splite after "Data publikacji:" this keyword......Grab time also

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(2)").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data złożenia oferty:
    # Onsite Comment -Note:Splite after "Data złożenia oferty:" this keyword..... Grab time also

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "tr > td:nth-child(3)").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.blue-header > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    






# Format 1 = https://ciech.logintrade.net/zapytania_email,1547951,a4566fcd82fc69bfb58790efc2744d78.html 
        




    # Onsite Field -None
    # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#container').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
# Onsite Field -None
# Onsite Comment -Note:Click on "div:nth-child(3) a" this button "Show contact detail" on page_detail than grab the data
# Ref_url=https://zepak.logintrade.net/zapytania_email,1548762,8b0c7b01cda6807dfd3069d7baf24d43.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#container'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.company').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Add "#firma_info > h3:nth-child(3)" both selector

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#firma_info > h3:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Purchaser
        # Onsite Comment -Note:Split between "Purchaser:" and "Phone:"
            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#dane_osob > div:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Phone:
        # Onsite Comment -Note:Splite after "Phone:" this keyword

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#dane_osob > div:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -e-mail:
        # Onsite Comment -Note:Splite after "e-mail:" this keyword

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#dane_osob > div:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
# Ref_url= https://zepak.logintrade.net/zapytania_email,1548232,22b1802feb0cb5e9da6460f167b75222.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#aukcja2 > table:nth-child(17)'):
            lot_details_data = lot_details()
        # Onsite Field -Products: >> Index
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(17) tr > td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products: >> Product name
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(17) tr > td:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products: >> Quantity
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(17) tr > td:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products: >> Unit
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(17) tr > td:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None
        # Ref_url= https://hutabankowa.logintrade.net/zapytania_email,1547941,4d643b7d2d5d191859daf2ffc10693c4.html
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#container'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Offer evaluation criteria
                    # Onsite Comment -Note:"Price - 85%" here grab only "Price"

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Offer evaluation criteria")]//following::ol[1]').text
			
                    # Onsite Field -Offer evaluation criteria
                    # Onsite Comment -Note:"Price - 85%" here grab only "85%"

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.XPATH, '//*[contains(text(),"Offer evaluation criteria")]//following::ol[1]').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Products:
# Onsite Comment -None
# Ref_url= https://hutabankowa.logintrade.net/zapytania_email,1548233,5fc93790ec8e66f4482e9c0175ce6d9e.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#aukcja2 > table:nth-child(17)'):
            attachments_data = attachments()
        # Onsite Field -Attachment/Link
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(17) tr > td:nth-child(6) a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachment/Link
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'table:nth-child(17) tr > td:nth-child(6) a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -Attachments:
# Onsite Comment -None
# Ref_url= https://ciech.logintrade.net/zapytania_email,1547951,a4566fcd82fc69bfb58790efc2744d78.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#aukcja2 > ul'):
            attachments_data = attachments()
        # Onsite Field -Attachments:
        # Onsite Comment -Note:Don't take file extention

            try:
                attachments_data.file_name = page_details.find_element(By.CSS_SELECTOR, 'ul > li > p > a').text
            except Exception as e:
                logging.info("Exception in file_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments:
        # Onsite Comment -Note:Take only file extention

            try:
                attachments_data.file_type = page_details.find_element(By.CSS_SELECTOR, 'ul > li > p > a').text
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments:
        # Onsite Comment -None

            try:
                attachments_data.file_size = page_details.find_element(By.CSS_SELECTOR, 'ul > li > em').text
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Attachments:
        # Onsite Comment -None

            attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'ul > li > p > a').get_attribute('href')
            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    



# Format 2 = https://grupasmithfield.logintrade.net/portal,szczegolyZapytaniaOfertowe,60c265ef7be0ee671026cb687fe9961e.html
    



    # Onsite Field -None
    # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainPageContent').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

# Onsite Field -None
# Onsite Comment -None
# Ref_url=https://cobra-europe.logintrade.net/portal,szczegolyZapytaniaOfertowe,aa3376cafd1b0a83a8672daddf60b580.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#sectionBuyer'):
            customer_details_data = customer_details()
        # Onsite Field -None
        # Onsite Comment -None

            try:
                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td.name > div > div.company').text
            except Exception as e:
                logging.info("Exception in org_name: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Add "#buyerInfo > div:nth-child(3)" both selector

            try:
                customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, '#buyerInfo > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -Note:Splite after "Buyer:" this keyword

            try:
                customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(1)').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -landline
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(2)').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -mobile phone
        # Onsite Comment -None

            try:
                customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(3)').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -e-mail
        # Onsite Comment -None

            try:
                customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, '#buyerContact > div:nth-child(4)').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
        
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
# Ref_url=https://adama.logintrade.net/portal,szczegolyZapytaniaOfertowe,c6337049853d25633ca87dbc533eec92.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainPageContent'):
            lot_details_data = lot_details()
        # Onsite Field -Products >> Product
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'td.product.full').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products >> Quantity
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'td.quantity').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products >> Unit
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity_uom = page_details.find_element(By.CSS_SELECTOR, 'td.units').text
            except Exception as e:
                logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -None
        # Ref_url=https://hutabankowa.logintrade.net/zapytania_email,1547941,4d643b7d2d5d191859daf2ffc10693c4.html
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainPageContent'):
                    lot_criteria_data = lot_criteria()
		
                    # Onsite Field -Offer evaluation criteria
                    # Onsite Comment -Note:"Price - 85%" here grab only "Price"

                    lot_criteria_data.lot_criteria_title = page_details.find_element(By.CSS_SELECTOR, 'sectionCriteria').text
			
                    # Onsite Field -Offer evaluation criteria
                    # Onsite Comment -Note:"Price - 85%" here grab only "85%"

                    lot_criteria_data.lot_criteria_weight = page_details.find_element(By.CSS_SELECTOR, 'sectionCriteria').text
			
                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                pass
			
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None
# Ref_url=https://sefako.logintrade.net/portal,szczegolyAukcje,25018207e858cf394f26195a3689b160.html
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#mainPageContent'):
            lot_details_data = lot_details()
        # Onsite Field -Products >> Product Index/No.
        # Onsite Comment -None

            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, 'td.index').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products >> Product
        # Onsite Comment -None

            try:
                lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, 'td.product').text
            except Exception as e:
                logging.info("Exception in lot_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products >> Quantity
        # Onsite Comment -None

            try:
                lot_details_data.lot_quantity = page_details.find_element(By.CSS_SELECTOR, 'td.quantity').text
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -Products >> Maximum price
        # Onsite Comment -None

            try:
                lot_details_data.lot_grossbudget_lc = page_details.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
            except Exception as e:
                logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
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
    urls = ["https://platformazakupowa.logintrade.pl/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        for page_no in range(2,50):
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="offers-table"]/table/tbody/tr'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="offers-table"]/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="offers-table"]/table/tbody/tr')))[records]
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
                WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="offers-table"]/table/tbody/tr'),page_check))
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