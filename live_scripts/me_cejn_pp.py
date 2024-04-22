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
from selenium.webdriver.support.ui import Select


NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "me_cejn_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global notice_type
    notice_data = tender()
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ME'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    notice_data.main_language = 'ME'
    notice_data.script_name = 'me_cejn_pp'

    notice_data.notice_type = 3

    notice_data.procurment_method = 2
    
    notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(1)').text
    
    try:
        notice_data.notice_url = 'https://cejn.gov.me/plans/view-plan/'+str(notice_data.notice_no)
        fn.load_page(page_details,notice_data.notice_url,80)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__)) 
        pass
    
    try:
        clk = page_details.find_element(By.XPATH,'//*[@id="mat-dialog-0"]/app-message-info/div[3]/button').click()
    except:
        pass
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR,'#mat-tab-content-0-0 > div > div > div.mat-elevation-z1.main2 > div > div > div.kolona2 > table > tbody > tr td:nth-child(3) span:nth-child(1)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in notice_title: {}".format(type(e).__name__)) 
        pass
       
    try:
        publish_date =  tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(5)').text
        notice_data.publish_date = datetime.strptime(publish_date, '%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__)) 
        pass
    logging.info(notice_data.publish_date)
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR,'td:nth-child(3)').text
        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH,"//*[contains(text(),'Adresa')]//following::div[1]").text
        except:
            pass  
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH,"//*[contains(text(),'Telefon')]//following::div[1]").text
        except:
            pass
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH,"//*[contains(text(),'E-mail')]//following::div[1]").text
        except:
            pass
        try:
            customer_details_data.org_fax = page_details.find_element(By.XPATH,"//*[contains(text(),'Fax')]//following::div[1]").text
        except:
            pass
        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH,"//*[contains(text(),'Grad')]//following::div[1]").text
        except:
            pass
        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH,"//*[contains(text(),'Poštanski broj')]//following::div[1]").text
        except:
            pass
        customer_details_data.org_website = page_details.find_element(By.XPATH,"//*[contains(text(),'Internet adresa')]//following::div[1]").text
        customer_details_data.contact_person = page_details.find_element(By.XPATH,"//*[contains(text(),'Odgovorna osoba')]//following::div[1]").text
        customer_details_data.org_country = 'ME'
        customer_details_data.org_language = 'ME'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
        
    try:
        est_amount = page_details.find_element(By.XPATH, "//*[contains(text(),'Ukupna vrijednost plana')]//following::div[1]").text
        est_amount = re.sub("[^\d\.\,]","",est_amount).replace('.','')
        if ',' in est_amount:
            est_amount = est_amount.replace(',','')
        if '.' in est_amount:
            est_amount = est_amount.replace('.','')
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
        notice_data.grossbudgeteuro = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__)) 
        pass  
    
    try:
        vat = page_details.find_element(By.XPATH,"//*[contains(text(),'Ukupna vrijednost PDV')]//following::div[1]").text
        vat = re.sub("[^\d\.\,]","",est_amount)
        vat =vat.replace(',','').replace('.','')
        notice_data.vat = float(vat)
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__)) 
        pass 
    try:
        all_in_on = []
        notice_data.class_at_source = 'CPV'
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'td:nth-child(3)'):
            cpv_data =single_record.text.split('\n')[1:]
            all_in_on.extend(cpv_data)

        cpv_at_source = ''
        class_codes_at_source = ''
        for code1 in all_in_on:
            cpvs_data = cpvs()
            cpv_regex = re.findall(r'\d{8}',code1)[0]
            cpvs_data.cpv_code = cpv_regex
            cpv_at_source += cpv_regex
            cpv_at_source += ','

            class_codes_at_source += cpv_regex  
            class_codes_at_source += ','
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_at_source.rstrip(',')
        notice_data.class_codes_at_source = class_codes_at_source.rstrip(',')
    except:
        pass
    try:
        all_in_on1= []
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'td:nth-child(3)'):
            cpv_data =single_record.text.split('\n')[1:]
            all_in_on1.extend(cpv_data)
        class_title_at_source  = ''
        for single_record1 in all_in_on1:
            cpv_regex = re.findall("\d+\s*-\s*(.+)", single_record1)[0]
            class_title_at_source += cpv_regex
            class_title_at_source +=','
        notice_data.class_title_at_source = class_title_at_source.rstrip(',')
    except:
        pass
    try:
        lot_number=1
        for single_record in page_details.find_elements(By.CSS_SELECTOR,'#mat-tab-content-0-0 > div > div > div.mat-elevation-z1.main2 > div > div > div.kolona2 > table > tbody > tr'):
            lot_details_data=lot_details()
            lot_details_data.lot_number = lot_number
            lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(3) span:nth-child(1)').text
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            try:
                lot_details_data.lot_grossbudget_lc  = single_record.find_element(By.CSS_SELECTOR,'td:nth-child(4)').text.split('EUR')[0]
                lot_details_data.lot_grossbudget_lc =lot_details_data.lot_grossbudget_lc.replace('.','').replace(',','.')
                lot_details_data.lot_grossbudget_lc = float(lot_details_data.lot_grossbudget_lc)
            except:
                pass
            all_in_on = []
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'td:nth-child(3)'):
                cpv_data =single_record.text.split('\n')[1:]
                all_in_on.extend(cpv_data)

            lot_class_codes_at_source = ''
            lot_cpv_at_source = ''
            for code1 in all_in_on:
                lot_cpvs_data = lot_cpvs() 
                cpv_regex = re.findall(r'\d{8}',code1)[0]
                lot_cpvs_data.lot_cpv_code  = cpv_regex


                lot_cpv_at_source += cpv_regex  
                lot_cpv_at_source += ','

                lot_class_codes_at_source += cpv_regex  
                lot_class_codes_at_source += ','

                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            lot_details_data.lot_class_codes_at_source = lot_class_codes_at_source.rstrip(',')
            lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number +=1 
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.XPATH,'/html/body/app-root/div/app-header/div/mat-sidenav-container/mat-sidenav-content/div/main/app-plan-view/mat-card/mat-card-content/div/mat-tab-group').get_attribute('outerHTML')
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__)) 
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

    urls = ['https://cejn.gov.me/plans'] 

    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            clk = page_main.find_element(By.XPATH,'//*[@id="mat-dialog-0"]/app-message-info/div[3]/button').click()
            time.sleep(5)
        except:
            pass
    
        try:
            for page_no in range(1,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > app-root > div > app-header > div > mat-sidenav-container > mat-sidenav-content > div > main > app-plan-list > form > div > mat-card > mat-card-content > div > mat-drawer-container > mat-drawer-content > div.table-container.plans-table > div:nth-child(1) > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > app-root > div > app-header > div > mat-sidenav-container > mat-sidenav-content > div > main > app-plan-list > form > div > mat-card > mat-card-content > div > mat-drawer-container > mat-drawer-content > div.table-container.plans-table > div:nth-child(1) > table > tbody > tr')))
                length = len(rows) 
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'body > app-root > div > app-header > div > mat-sidenav-container > mat-sidenav-content > div > main > app-plan-list > form > div > mat-card > mat-card-content > div > mat-drawer-container > mat-drawer-content > div.table-container.plans-table > div:nth-child(1) > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break

                try:   
                    next_page = WebDriverWait(page_main, 10).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/div/app-header/div/mat-sidenav-container/mat-sidenav-content/div/main/app-plan-list/form/div/mat-card/mat-card-content/div/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-paginator/div/div/div[2]/button[3]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    time.sleep(20)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'body > app-root > div > app-header > div > mat-sidenav-container > mat-sidenav-content > div > main > app-plan-list > form > div > mat-card > mat-card-content > div > mat-drawer-container > mat-drawer-content > div.table-container.plans-table > div:nth-child(1) > table > tbody > tr'),page_check))
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