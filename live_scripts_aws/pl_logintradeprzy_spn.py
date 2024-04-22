
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "pl_logintradeprzy_spn"
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
from selenium.webdriver.chrome.options import Options 

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "pl_logintradeprzy_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'pl_logintrade_spn'
   
    notice_data.main_language = 'PL'
   
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'PL'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    
    notice_data.currency = 'PLN'
    
    notice_data.procurement_method = 2
    
    try:
        data = page_main.find_element(By.CSS_SELECTOR, "#content_white > div:nth-child(1) > h2").text
    except:
        pass
    
    try:
        if "Open enquiries" in data:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        
        elif "E-auctions" in data:
            
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date_1: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
   
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_no = re.findall('\w{1}\d+/\d{6}',notice_no)[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        if "Open enquiries" in data:
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
            notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
            
        elif "E-auctions" in data:
        
            notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
            notice_deadline = re.findall('\d{4}-\d+-\d+ \d+:\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H:%M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        if "Open enquiries" in data:
            org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text
        elif "E-auctions" in data:
            org_name = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text
    except Exception as e:
        logging.info("Exception in org_name: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        detail_page = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"td:nth-child(2) > a")))
        page_main.execute_script("arguments[0].click();",detail_page)
        time.sleep(5)
        notice_data.notice_url = page_main.find_element(By.CSS_SELECTOR, '#dialog_wybierz_aukcje > ul > li:nth-child(1) > a').get_attribute("href")
    except Exception as e:  
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass
    
    try:    
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        time.sleep(5)

        try:
            ok_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="infoPanel"]/a')))
            page_details.execute_script("arguments[0].click();",ok_click)
            time.sleep(5)
        except:
            pass

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content_white').get_attribute("outerHTML")                     
        except:
            pass

        try:              
            customer_details_data = customer_details()
            customer_details_data.org_country = 'PL'
            customer_details_data.org_language = 'PL'
            customer_details_data.org_name = org_name

            try:
                Show_contact_details_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#pokaz_dane_kontaktowe")))
                page_details.execute_script("arguments[0].click();",Show_contact_details_click)
                time.sleep(3)
                
                try:
                    customer_details_data.contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Purchaser:')]//following::div[1]").text.split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Purchaser:')]//following::div[1]").text.split('Phone:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                try:
                    customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Purchaser:')]//following::div[1]").text.split('e-mail:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass
            except:
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Enquiry contents:')]//following::div[1]").text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except:
            try:
                notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Auction description:')]//following::div[1]").text
                notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
            except Exception as e:
                logging.info("Exception in local_description: {}".format(type(e).__name__))
                pass

        try:
            lot_data = page_details.find_element(By.XPATH, "(//*[contains(text(),'roducts:')]//following::table)[1]")
            lot_number = 1
            for single_record in lot_data.find_elements(By.CSS_SELECTOR, " tbody > tr")[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                    lot_quantity = re.sub("[^\d\.\,]","",lot_quantity)
                    lot_details_data.lot_quantity =float(lot_quantity.replace('.','').replace(',','.').strip())
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
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

        try:              
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Offer evaluation criteria')]//following::ol/li"):
                tender_criteria_data = tender_criteria()

                tender_criteria_data.tender_criteria_title = single_record.text.split('-')[0].strip()

                if "price" in tender_criteria_data.tender_criteria_title.lower():
                    tender_criteria_data.tender_is_price_related = True

                tender_criteria_weight = single_record.text.split('-')[1].replace('%','').strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass

        try:
            for single_record in page_details.find_elements(By.XPATH, "//*[contains(text(),'Attachments:')]//following::ul[1]/li"):
                attachments_data = attachments()

                attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, "p > a").get_attribute("href")

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, "p > a").text

                try:
                    attachments_data.file_type = attachments_data.file_name.split('.')[-1].strip()
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                try:
                    attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, "em").text
                except Exception as e:
                    logging.info("Exception in file_size: {}".format(type(e).__name__))
                    pass

                if attachments_data.external_url != '':
                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized'] 
options = Options() 
for argument in arguments: 
    options.add_argument(argument) 
page_main = webdriver.Chrome(options=options) 
page_details = webdriver.Chrome(options=options) 

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    login_url = "https://przyjazn.logintrade.net/rynek,zapytania.html"

    logging.info('----------------------------------')
    logging.info(login_url)
    fn.load_page_expect_xpath(page_main, login_url,'//*[@id="panelP"]/div[1]/form/fieldset/label[1]',10)
    page_main.find_element(By.XPATH,'//*[@id="loginInputId"]').send_keys('akanksha.a')
    time.sleep(2)
    page_main.find_element(By.XPATH,'//*[@id="panelP"]/div[1]/form/fieldset/input[2]').send_keys('Ak@123456')

    submit_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="panelP"]/div[1]/form/fieldset/input[3]')))
    page_main.execute_script("arguments[0].click();",submit_click)
    time.sleep(5) 

    try:
        fn.load_page_expect_xpath(page_details, login_url,'//*[@id="panelP"]/div[1]/form/fieldset/label[1]',10)

        page_details.find_element(By.XPATH,'//*[@id="loginInputId"]').send_keys('akanksha.a')
        time.sleep(2)
        page_details.find_element(By.XPATH,'//*[@id="panelP"]/div[1]/form/fieldset/input[2]').send_keys('Ak@123456')

        submit_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="panelP"]/div[1]/form/fieldset/input[3]')))
        page_details.execute_script("arguments[0].click();",submit_click)
        time.sleep(5)  
    except:
        pass
    
    sub_url = page_main.find_element(By.CSS_SELECTOR, '#content > ul > li:nth-child(1) > a').get_attribute("href")
    fn.load_page(page_main, sub_url, 50)
    logging.info(sub_url)
    
    lst=[0,1,2]
    for no in lst:
        url1 = page_main.find_elements(By.CSS_SELECTOR, '#container > div.topDostawcaMenuPanel > ul > li > a')[no]
        sub_url1 = url1.get_attribute("href")
        fn.load_page(page_main, sub_url1, 50)
        logging.info(sub_url1)
    
        try:
            for page_no in range(2,20):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'table:nth-child(2) > tbody > tr:nth-child(3)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table:nth-child(2) > tbody > tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table:nth-child(2) > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'table:nth-child(2) > tbody > tr:nth-child(3)'),page_check))
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
