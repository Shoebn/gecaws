#NOTE- USE VPN... Select "DATA PUBLICARE" >>>> select previous and current date >>>>  FILTREAZA 

from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ro_elicitatiepi_spn"
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ro_elicitatiepi_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'ro_elicitatiepi_spn'
    notice_data.main_language = 'RO'
    notice_data.currency = 'RON'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)

    notice_data.notice_type = 3
    notice_data.procurement_method = 2
    
    # Onsite Field -Data publicare:
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) strong > span").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
     
    
    # Onsite Field -Tip contract:
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div:nth-child(2) > strong').text
        if 'Lucrari' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Furnizare' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Servicii' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 > h2 > span > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:              
        cpvs_data = cpvs()

        cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div.col-md-6 > strong').text
        cpv_code = re.findall('\d{8}',cpv_code)[0]
        cpvs_data.cpv_code = cpv_code
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        
        notice_data.cpv_at_source = cpvs_data.cpv_code+','
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-6 > span > strong').text
    except:
        pass
    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div.col-md-6 > strong').text
    except:
        pass

    try:
        notice_url_click = WebDriverWait(tender_html_element,120).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.col-md-9 > h2 > span > a')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(10)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="section-1"]/div[2]/h2[1]'))).text
        
     # Onsite Field -Bando
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = notice_no
    except:
        notice_data.notice_no = notice_data.notice_url.split('/')[-1].strip()

    
    # Onsite Field -None
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ---- "//*[@id="container-sizing"]/div[5]/div/div[2]/div/div"

    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#container-sizing').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    
    # Onsite Field -Tip contract:
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_main.find_element(By.XPATH, '//*[contains(text(),"referinta:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Data expedierii prezentului anunt
    # Onsite Comment -None

    try:
        dispatch_date = page_main.find_element(By.XPATH, '''//*[contains(text(),"Data expedierii prezentului")]//following::span[1]''').text
        dispatch_date = re.findall('\d+.\d+.\d{4} \d+:\d+',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.dispatch_date)
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'RO'
        customer_details_data.org_country = "RO"

        customer_details_data.org_name = org_name
        print("customer_details_data.org_name::",customer_details_data.org_name)

        # Onsite Field -I.5) Activitatea principala
        # Onsite Comment -None
  
        try:                                                                                    
            customer_details_data.customer_main_activity = page_main.find_element(By.XPATH, '(//*[contains(text(),"Activitatea principala")])[1]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

        # Onsite Field -Denumire si adrese
        # Onsite Comment -Note: splite data between  Adresa till Localitate

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        # Onsite Field -E-mail
        # Onsite Comment -None

        try:
            customer_details_data.org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Telefon
    # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Denumire si adrese
    # Onsite Comment -Note:Splite from Fax till  Punct(e) de contact

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '(//*[contains(text(),"Fax:")])[2]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Localitate
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '(//*[contains(text(),"Localitate:")])[1]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Cod postal
    # Onsite Comment -None 

        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod Postal:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Cod NUTS
    # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod NUTS")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        # Onsite Field -Tip autoritate contractanta
    # Onsite Comment -None

        try:
            customer_details_data.type_of_authority_code = page_main.find_element(By.XPATH, '((//*[contains(text(),"Tip autoritate contractanta")])[2]//following::span[1])[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    # Onsite Field -Valoarea totala estimata:
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/pi-notice/view/v2/100062706"

    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Valoarea totala")]//following::span[2]').text
        if "Max:" in est_amount:
            split_est_amount = est_amount.split("Max:")[1].strip()
            est_amount = re.sub("[^\d\.\,]","",split_est_amount)
            notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        else:
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount = float(est_amount.replace('.','').replace(',','.').strip())
            notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    # Onsite Field -Descriere succinta
    # Onsite Comment -None
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Descriere succinta")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:              
        custom_tags_data = custom_tags()

    # Onsite Field -Cod fiscal
    # Onsite Comment -None

        tender_custom_tag_company_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Fiscal")]//following::span[1]').text
        custom_tags_data.tender_custom_tag_company_id = int(tender_custom_tag_company_id)

        custom_tags_data.custom_tags_cleanup()
        notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass

#Onsite Field -
# Onsite Comment - Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data ...........ref url "https://www.e-licitatie.ro/pub/notices/pi-notice/view/v2/100062704

    try:
        lot_number = 1
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.c-lots-list__items.ng-scope'):
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            
            
            try:
                lot_cpvs_data = lot_cpvs()

                lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'div.c-lots-list__item__value.truncate.ng-binding > strong').text
                lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]  
                cpvs_data = cpvs()
                cpvs_data.cpv_code = lot_cpvs_data.lot_cpv_code 
                cpvs_data.cpvs_cleanup()

                notice_data.cpvs.append(cpvs_data)
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
                notice_data.cpv_at_source = notice_data.cpv_at_source+','+lot_cpvs_data.lot_cpv_code
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
            
            eye_clk = single_record.find_element(By.CSS_SELECTOR, 'div.col-md-2.col-md-push-10 > div > div > button').click()

        # Onsite Field -Lot nr.
        # Onsite Comment -split the actual number from the title

            try:
                lot_details_data.lot_actual_number = page_main.find_element(By.XPATH, '//*[contains(text(),"Lot nr.")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -II.2.1) Titlu
        # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

            lot_details_data.lot_title = page_main.find_element(By.XPATH, '//*[contains(text(),"Titlu ")]//following::span[1]').text
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            lot_details_data.contract_type = notice_data.notice_contract_type

        # Onsite Field -Descrierea achizitiei publice
        # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Descrierea achizitiei publice")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -CPV code
        # Onsite Comment -None

            try:
                lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Codul NUTS")]//following::span[1]').text
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass

        # Onsite Field - Informatii suplimentare
        # Onsite Comment -split from "-" till "lei fara TVA"

            try:
                lot_netbudget_lc = page_main.find_element(By.XPATH, '//*[contains(text(),"Informatii suplimentare")]//following::span[1]').text.split('-')[-1].strip()
                lot_netbudget_lc = re.sub("[^\d\.\,]","",lot_netbudget_lc)
                lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(',','.').replace('.','').strip())
            except Exception as e:
                logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                pass
                                                          

            try:
                lot_click_back = page_main.find_element(By.XPATH, "(//a[@class='k-window-action k-link'])[2]").click()
                time.sleep(5)
            except:
                pass

            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except:
        try:              
            lot_details_data = lot_details()

            lot_details_data.lot_title = page_main.find_element(By.XPATH, '((//*[contains(text(),"Titlu")])[1]//following::div[1]/div)[1]').text
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
            lot_details_data.contract_type = notice_data.notice_contract_type

        # Onsite Field -Descrierea achizitiei publice
        # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '(//*[contains(text(),"Descrierea achizitiei publice")])[1]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass


            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    try:
        back = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.ng-isolate-scope.btn.btn-default.carbon.shutter-out-vertical")))
        page_main.execute_script("arguments[0].click();",back)
        time.sleep(3)
    except:
        pass
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[5]/div/div[2]/div/div'))).text

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body

options = webdriver.ChromeOptions()
options.add_extension("C:/Users/Administrator/home/Urban-Free-VPN-proxy-Unblocker---Best-VPN.crx")
page_main = webdriver.Chrome(options=options)
page_main.maximize_window()
time.sleep(20)

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-licitatie.ro/pub/notices/pi-notices"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        status_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="container-sizing"]/div[3]/div[2]/ng-transclude/div[2]/div[3]/div/div[2]/span/span/span/span'))).click()    
        time.sleep(5)

        action = ActionChains(page_main)
 
        action.send_keys(Keys.ENTER) 
        time.sleep(5)

        action.perform()
                                                                                            
        status_click_2 = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="container-sizing"]/div[3]/div[2]/ng-transclude/div[2]/div[3]/div/div[1]/span/span/span/span')))
        page_main.execute_script("arguments[0].click();",status_click_2)
        time.sleep(5)

        action = ActionChains(page_main)

        action.send_keys(Keys.ARROW_LEFT)
        time.sleep(2)
        action.send_keys(Keys.ARROW_LEFT)
        time.sleep(2)
        action.send_keys(Keys.ARROW_LEFT)
        time.sleep(2)
        action.send_keys(Keys.ENTER) 
        time.sleep(5)

        action.perform()
    
        search = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="THE-SEARCH-BUTTON"]')))
        page_main.execute_script("arguments[0].click();",search)
        time.sleep(10)
        
        try:
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[5]/div/div[2]/div/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[5]/div/div[2]/div/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    output_json_file.copyFinalJSONToServer(output_json_folder)
