from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "az_etender_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from selenium.webdriver.chrome.options import Options
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "az_etender_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'az_etender_spn'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AZ'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'AZ'
    
    notice_data.currency = 'AZN'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4
    
    notice_data.class_at_source = "USL"
    
    notice_data.class_codes_at_source = "50331000-4"

    notice_data.class_title_at_source = "Telekommunikasiya xətlərinin təmiri və texniki xidməti"
    
    # Onsite Field -Satınalma predmeti
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Başlama tarixi
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Bitmə tarixi
    # Onsite Comment -None

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        url1 = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute("href").split("detail/")[1].strip()  
        notice_data.notice_url ="https://etender.gov.az/main/competition/detail/"+str(url1)
        fn.load_page(page_details,notice_data.notice_url,90)
        time.sleep(5)
        logging.info(notice_data.notice_url)
    except:
        pass
    
    # Onsite Field -Bitmə tarixi
    # Onsite Comment -None

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'app-competition-detail > main').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    # Onsite Field -Müsabiqənin nömrəsi:
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Müsabiqənin nömrəsi:")]//following::div[1]').text
    except Exception as e:
        notice_data.notice_no = notice_data.notice_url.split("detail/")[1].strip()
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -1.split notice_no from notice_url.	here "https://etender.gov.az/main/competition/detail/297450" take only "297450" in notice_no.

    
    # Onsite Field -Zərflərin açılış tarixi və vaxtı:
    # Onsite Comment -None

    try:
        document_opening_time = page_details.find_element(By.XPATH, '//*[contains(text(),"Zərflərin açılış tarixi və vaxtı:")]//following::div[1]').text
        document_opening_time = re.findall('\d+.\d+.\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
    except Exception as e:
        logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
        pass

    # Onsite Field -Çatdırılma müddəti
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Çatdırılma müddəti")]//following::app-tooltip[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'AZ'
        customer_details_data.org_country = 'AZ'
        # Onsite Field -Satınalan təşkilatın adı
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

    # Onsite Field -Satınalan təşkilatın VÖEN-i:
    # Onsite Comment -None

        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Satınalan təşkilatın VÖEN-i:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Satınalan təşkilatın ünvanı:
    # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Satınalan təşkilatın ünvanı:")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.contact_person = page_details.find_element(By.CSS_SELECTOR, 'section.section__6 > div.container > div:nth-child(2) > div:nth-child(1)').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'section.section__6 > div.container > div:nth-child(2) > div:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'section.section__6 > div.container > div:nth-child(2) > div:nth-child(4)').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -ref_url:"https://etender.gov.az/main/competition/detail/297454".

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'body > app-root > app-competition-detail > main > section.section__5 > div > div')[1:]:
            tender_criteria_data = tender_criteria()
            
        # Onsite Comment -1.here "Qiymət təklifi: 70 bal" take only "Qiymət təklifi" in title.
        # Onsite Comment -1.here "Texniki təklif: 30 bal" take only "Texniki təklif" in title.

            tender_criteria_title = single_record.text.split(":")[0].strip()
            tender_criteria_title = GoogleTranslator(source='ro', target='en').translate(tender_criteria_title)
            if 'technical' in tender_criteria_title.lower():
                tender_criteria_data.tender_criteria_title = 'technique'
            elif 'price' in tender_criteria_title.lower():
                tender_criteria_data.tender_criteria_title = 'price'

        # Onsite Comment -1.here "Qiymət təklifi: 70 bal" take only "70" in weight.
        # Onsite Comment -1.here "Texniki təklif: 30 bal" take only "30" in weight.
        
            tender_criteria_weight =single_record.text.split(":")[1].split("bal")[0].strip()
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
            
            if "price" in tender_criteria_data.tender_criteria_title:
                tender_criteria_data.tender_is_price_related = True
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    try:
        url = notice_data.notice_url.split("detail/")[1].strip()  
        Hamısına_bax_url ="https://etender.gov.az/main/competition/products/"+str(url)
        fn.load_page(page_details1,Hamısına_bax_url,90)
        time.sleep(5)
        logging.info(Hamısına_bax_url)
    except:
        pass
        
    try:
        notice_data.notice_text += page_details1.find_element(By.CSS_SELECTOR, 'section.section__1').get_attribute("outerHTML")                     
    except:
        pass
# # Onsite Field -None
# # Onsite Comment -1.click on "Hamısına bax" in page_details to take lot_details..		2.lot_details are present in multiple pages...
    try:
        range_lot=page_details1.find_element(By.XPATH, '(//a[@class="page"])[last()]').text
        lot=int(range_lot)

        for page_no in range(1,lot+1):                                                                          
            page_check = WebDriverWait(page_details1, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'body > app-root > app-competition-product > main > section > div > table > tbody > tr'))).text
            rows = WebDriverWait(page_details1, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > app-root > app-competition-product > main > section > div > table > tbody > tr')))
            length = len(rows)
            lot_number=1
            for records in range(0,length):
                single_record = WebDriverWait(page_details1, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > app-root > app-competition-product > main > section > div > table > tbody > tr')))[records]
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number

                  # Onsite Field -Başlıq
            # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            # Onsite Field -№
            # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Açıqlama
            # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > app-tooltip > div:nth-child(2) > p').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Miqdar
            # Onsite Comment -None

                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_quantity = re.sub("[^\d\.\,]","",lot_quantity)
                    lot_quantity=lot_quantity.replace('.','')
                    lot_details_data.lot_quantity = float(lot_quantity.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ölçü vahidi
            # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1

            if lot == page_no:
                break
            try:
                next_page = WebDriverWait(page_details1, 50).until(EC.element_to_be_clickable((By.XPATH,'(//a[@class="next"])[last()]')))
                page_details1.execute_script("arguments[0].click();",next_page)
                logging.info("Next page of lot")
                WebDriverWait(page_details1, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > app-root > app-competition-product > main > section > div > table > tbody > tr'),page_check))
            except:
                pass
    except:
        try:
            lot_number = 1
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, ' body > app-root > app-competition-product > main > section > div > table > tbody > tr'):
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                
                  # Onsite Field -Başlıq
            # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            # Onsite Field -№
            # Onsite Comment -None

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Açıqlama
            # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3) > app-tooltip > div:nth-child(2) > p').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Miqdar
            # Onsite Comment -None

                try:
                    lot_quantity = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    lot_quantity = re.sub("[^\d\.\,]","",lot_quantity)
                    lot_quantity=lot_quantity.replace('.','')
                    lot_details_data.lot_quantity = float(lot_quantity.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Ölçü vahidi
            # Onsite Comment -None

                try:
                    lot_details_data.lot_quantity_uom = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text
                except Exception as e:
                    logging.info("Exception in lot_quantity_uom: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
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
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details =  webdriver.Chrome(options=options) 
page_details1 =  webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://etender.gov.az/main/competitions/1/0"] 
    for url in urls:
        fn.load_page(page_main, url, 90)
        time.sleep(4)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            for page_no in range(2,7):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/app-root/app-competitions/main/section/div/div[2]/div/app-table/div[1]/div/table/tbody/tr'),page_check))
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
