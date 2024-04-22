 #NOTE- USE VPN... Select "DATA PUBLICARE" >>>> select previous and current date >>>>  FILTREAZA 
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ro_elicitatiesad_spn"
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
import gec_common.Doc_Download_VPN
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ro_elicitatiesad_spn"
Doc_Download = gec_common.Doc_Download_VPN.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'ro_elicitatiesad_spn'

    notice_data.currency = 'ROM'

    notice_data.procurement_method = 2

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)

    notice_data.main_language = 'RO'
 
    notice_data.notice_type = 4
    
    # Onsite Field -DATA PUBLICARE
    # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-1.margin-top-10 > div:nth-child(2)").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -NUMAR ANUNT
    # Onsite Comment -also take notice_no from notice url

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-1.margin-top-10 > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Durata
    # Onsite Comment -None

    try:
        notice_data.contract_duration = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > strong:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    # Onsite Field -Tipul contractului
    # Onsite Comment -"Lucrari=Works","Furnizare=Supply","Servicii=Service" if there are multiple type in single data eg "Furnizare / Cumparare" split each and map

    try:              
        cpvs_data = cpvs()
# Onsite Field -None
# Onsite Comment -None

        try:
            cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, ' div > div.col-md-9.padding-right-0 > div > div:nth-child(2)').text
            cpv_code = re.findall('\d{8}',cpv_code)[0]
            cpvs_data.cpv_code = cpv_code
            notice_data.cpv_at_source = cpvs_data.cpv_code
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_url_click = WebDriverWait(tender_html_element,120).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div:nth-child(1) > div > h2 > a')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(10)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        pass

    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div[1]/div/div[2]/div/div[5]/div[4]/div[1]/div[2]/ng-transclude'))).text
    
    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, '(//*[contains(text(),"contractului")]//following::span[1])[1]').text
        if 'Lucrari' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Furnizare' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Servicii' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Furnizare / Cumparare' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text()," succinta")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

        # Onsite Field -Numar de referinta
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Numar de referinta")]//following::span[1]').text
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

    
    
    # Onsite Comment -along with notice text (page detail) also take data from tender_html_element  (main page) ----"//*//*[@id="container-sizing"]/div[9]/div"
    try:
        notice_data.notice_text += page_main.find_element(By.XPATH, '/html/body').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')



            # Onsite Field -Valoarea totala estimata:
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/pi-notice/view/v2/100062706"

    try:
        est_amount = page_main.find_element(By.XPATH, '//*[contains(text(),"Valoarea totala")]//following::span[2]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass

    try:
        funding_agency = page_main.find_element(By.XPATH, '(//*[contains(text()," Informatii despre fondurile Uniunii Europene")]//following::span[2])[1]').text
        if 'Nu' not in funding_agency:
            funding_agency_data = funding_agencies()
            funding_agency_data.funding_agency = 1344862
            funding_agency_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agency_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))


# Onsite Field -None
# Onsite Comment -None

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Tara
    # Onsite Comment -None


        customer_details_data.org_country = 'RO'
        customer_details_data.org_language = 'RO'
    # Onsite Field -Autoritate contractanta
    # Onsite Comment -take data which is after "Autoritate contractanta"

        customer_details_data.org_name = page_main.find_element(By.CSS_SELECTOR, 'ul.ng-scope > li').text
      
    # Onsite Field -Adresa principala (URL)
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa Internet ")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
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
    # Onsite Comment -Note:Splite after Fax

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    # Onsite Field -Localitate
    # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Localitate:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Cod postal
    # Onsite Comment -

        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod postal:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass


    # Onsite Field -Activitate principala
    # Onsite Comment -None

        try:
            customer_details_data.customer_main_activity = page_main.find_element(By.XPATH, '//*[contains(text(),"Activitate ")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass


    # Onsite Field -Cod NUTS
    # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod NUTS")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass


        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        custom_tags_data = custom_tags()
    # Onsite Field -Cod fiscal
    # Onsite Comment -None

        try:
            custom_tags_data.tender_custom_tag_company_id = page_main.find_element(By.XPATH, '(//*[contains(text(),"Cod fiscal")])[1]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in tender_custom_tag_company_id: {}".format(type(e).__name__))
            pass

        custom_tags_data.custom_tags_cleanup()
        notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass

# Onsite Field -ref url -"https://www.e-licitatie.ro/pub/sad/cnotice/view/100173802"
# Onsite Comment -None

    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.c-list-container__item.padding-left-0.padding-right-0.ng-scope > div'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -DESCRIERE
        # Onsite Comment -ref url -"https://www.e-licitatie.ro/pub/sad/cnotice/view/100173802"

            try:
                tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-md-5.ng-binding').text
            except Exception as e:
                logging.info("Exception in tender_criteria_title: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -PONDERE-  just take values
        # Onsite Comment -ref url -"https://www.e-licitatie.ro/pub/sad/cnotice/view/100173802"

            try:
                tender_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-md-3 > div:nth-child(1)').text.split('%')[0].strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
            except Exception as e:
                logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                pass
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

# Onsite Field -click on "c-lots-list__item__header__title ng-binding" for detail
# Onsite Comment -None

    try:
        lot_pages = page_main.find_element(By.CSS_SELECTOR, 'div.row.margin-top-10.text-align-center > ul > li:nth-child(3) > a').text.split('of')[1].strip()
        lot_page_no = int(lot_pages)
        for page_no in range(1,lot_page_no+1):
            page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.c-lots-list__item'))).text
            rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.c-lots-list__item')))
            length = len(rows)

            lot_number = 1
            for records in range(0,length):
                single_record = page_main.find_elements(By.CSS_SELECTOR, 'div.c-lots-list__item')[records]
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            # Onsite Field -select data from lot page
            # Onsite Comment -None
                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'div.c-lots-list__item__content > div.row.margin-bottom-5').text
                    lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]  
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    notice_data.cpv_at_source = notice_data.cpv_at_source+ ','+ lot_cpvs_data.lot_cpv_code
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                eye_clk = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.c-lots-list__item__header.row > div > h4 > a')))
                page_main.execute_script("arguments[0].click();",eye_clk)
                time.sleep(6)

            # Onsite Field -Lot nr.
            # Onsite Comment -split the actual number from the title
                try:
                    lot_details_data.lot_actual_number =  WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(),"Numar lot:")]//following::span[1]'))).text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -II.2.1) Titlu
            # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

                lot_details_data.lot_title = page_main.find_element(By.XPATH, '(//*[contains(text(),"II.2.1) Titlu:")]//following::div/span[1])[1]').text
            # Onsite Field -Descrierea achizitiei publice
            # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

                try:
                    lot_details_data.lot_description = page_main.find_element(By.XPATH, '(//*[contains(text(),"Descrierea achizitiei publice")]//following::span[1])[3]').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -CPV code
            # Onsite Comment -None

                try:
                    lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '(//*[contains(text(),"Codul NUTS")]//following::span[1])[3]').text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

            # Onsite Field - Informatii suplimentare
            # Onsite Comment -split from "-" till "lei fara TVA"

                try:
                    lot_details_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Durata in luni:")]//following::span[1]').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Durata in luni:
            # Onsite Comment -None

                try:
                    lot_grossbudget = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.6) Valoarea estimata")]//following::span[2]').text
                    lot_grossbudget = re.sub("[^\d\.\,]","",lot_grossbudget)
                    lot_details_data.lot_grossbudget = float(lot_grossbudget)
                    lot_details_data.lot_grossbudget_lc = lot_details_data.lot_grossbudget
                except Exception as e:
                    logging.info("Exception in lot_grossbudget: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1

                lot_click_back = page_main.find_element(By.XPATH, "(//*[@class='k-window-action k-link'])[last()]").click()
                time.sleep(5)

            lot_next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.row.margin-top-10.text-align-center > ul > li:nth-child(4) > a')))
            page_main.execute_script("arguments[0].click();",lot_next_page)
            logging.info("lot_next_page")
            time.sleep(5)
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.c-lots-list__item'),page_check))
            logging.info("No next page")

    except:
        try:
            lot_number = 1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.c-lots-list__item'):
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
            # Onsite Field -select data from lot page
            # Onsite Comment -None
                try:
                    lot_cpvs_data = lot_cpvs()

                    lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'div.c-lots-list__item__content > div.row.margin-bottom-5').text
                    lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0]  
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    notice_data.cpv_at_source = notice_data.cpv_at_source + ',' + lot_cpvs_data.lot_cpv_code
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                eye_clk = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.c-lots-list__item__header.row > div > h4 > a')))
                page_main.execute_script("arguments[0].click();",eye_clk)
                time.sleep(5)
            # Onsite Field -Lot nr.
            # Onsite Comment -split the actual number from the title
                try:
                    lot_details_data.lot_actual_number =  WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[contains(text(),"Numar lot:")]//following::span[1]'))).text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

            # Onsite Field -II.2.1) Titlu
            # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

                lot_details_data.lot_title = page_main.find_element(By.XPATH, '(//*[contains(text(),"II.2.1) Titlu:")]//following::div/span[1])[1]').text
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                lot_details_data.contract_type = notice_data.notice_contract_type
            # Onsite Field -Descrierea achizitiei publice
            # Onsite Comment -Note:Cicking on "div.col-md-2.col-md-push-10 > div > div > button " for data

                try:
                    lot_details_data.lot_description = page_main.find_element(By.XPATH, '(//*[contains(text(),"Descrierea achizitiei publice")]//following::span[1])[3]').text
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

            # Onsite Field -CPV code
            # Onsite Comment -None

                try:
                    lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '(//*[contains(text(),"Codul NUTS")]//following::span[1])[3]').text
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

            # Onsite Field - Informatii suplimentare
            # Onsite Comment -split from "-" till "lei fara TVA"

                try:
                    lot_details_data.contract_duration = page_main.find_element(By.XPATH, '((//*[contains(text(),"II.2.7)")])[1]//following::div/div[1])[1]').text
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Durata in luni:
            # Onsite Comment -None

                        # Onsite Field - Criterii de atribuire:

        # Onsite Comment -ref url - "https://www.e-licitatie.ro/pub/sad/cnotice/view/100169003"

                try:
                    for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.c-list-container__item.padding-left-0.padding-right-0.ng-scope'):
                        lot_criteria_data = lot_criteria()

                        # Onsite Field -DESCRIERE
                        # Onsite Comment -None

                        lot_criteria_data.lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'div > div.row.margin-0 > div.col-md-5.ng-binding').text

                        # Onsite Field -PONDERE
                        # Onsite Comment -None

                        lot_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'div > div.row.margin-0 > div.col-md-3 > div:nth-child(1)').text.split('%')[0].strip()
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass


                try:
                    lot_click_back = page_main.find_element(By.XPATH, "(//*[@class='k-window-action k-link'])[last()]").click()
                    time.sleep(5)
                    WebDriverWait(page_main, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.c-lots-list__items > div.ng-scope'))).text
                except:
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.pull-left.margin-bottom-10.margin-left-20.ng-scope > strong'):
            attachments_data = attachments()
        # Onsite Field -Caiet de sarcini:
            try:
                file_type = single_record.find_element(By.CSS_SELECTOR,'a').text
                if 'pdf' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'doc' in file_type:
                    attachments_data.file_type = 'doc'
                elif 'xml' in file_type:
                    attachments_data.file_type = 'xml'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
            
            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR,'a').text.split(']')[1].split(attachments_data.file_type)[0].strip()

            external_url = WebDriverWait(single_record, 40).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a"))).click()
            time.sleep(25)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])            
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        back = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,"/html/body/div[1]/div/div[2]/div/div[3]/ul/li[3]/a")))
        page_main.execute_script("arguments[0].click();",back)
        time.sleep(3)
    except:
        pass


    WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div'))).text
    time.sleep(5)
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-licitatie.ro/pub/sad/sadList/1"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div'))).text
        try:
            status_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="container-sizing"]/div[7]/div[2]/ng-transclude/div[1]/div[4]/div/div[2]/div[1]/span/span/span/span'))).click()    
            time.sleep(5)

            action = ActionChains(page_main)

            action.send_keys(Keys.ENTER) 
            time.sleep(5)

            action.perform()
        except:
            pass
        
        try:
            status_click_2 = WebDriverWait(page_main, 60).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="container-sizing"]/div[7]/div[2]/ng-transclude/div[1]/div[4]/div/div[1]/div[1]/span/span/span/span')))
            page_main.execute_script("arguments[0].click();",status_click_2)
            time.sleep(5)

            action = ActionChains(page_main)

            action.send_keys(Keys.ARROW_LEFT)
            time.sleep(2)

            action.send_keys(Keys.ENTER) 
            time.sleep(5)

            action.perform()
        except:
            pass
        
        try:
            search = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="THE-SEARCH-BUTTON"]')))
            page_main.execute_script("arguments[0].click();",search)
            time.sleep(10)
        except:
            pass
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.u-items-list__item__properties'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.u-items-list__item__properties')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.u-items-list__item__properties')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.u-items-list__item__properties'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder) 
