#NOTE : click on "DATA PUBLICARE"/"PUBLICATION DATE" select previous and current date >>>> "FILTREAZA"
from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ro_elicitatie_spn"
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
import gec_common.Doc_Download_VPN as Doc_Download
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ro_elicitatie_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'ro_elicitatie_spn'
    
    notice_data.currency = 'RON'
    
    notice_data.main_language = 'RO'
    
    notice_data.procurement_method = 2
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.notice_type = 4
    
    # Onsite Field -NUMAR ANUNT
    # Onsite Comment -split notice_no from notice_url if notice no is not present

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-1.margin-top-10 > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DENUMIRE CONTRACT
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.padding-right-0 > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DATA PUBLICARE
    # Onsite Comment -grab the time which is present after date
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.col-md-1.margin-top-10 > div:nth-child(2) > span").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Data limita depunere
    # Onsite Comment -grab the time which is present after date

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(3) > strong").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 div > div:nth-child(2) > div').text.split("-")[1]
    
    # Onsite Field -Modalitatea de atribuire
    # Onsite Comment -just take data which is after "Modalitatea de atribuire:" till "CPV"

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 div > div:nth-child(2) > strong:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Tipul contractului
    # Onsite Comment -map it with ........."Lucrari=Works","Furnizare=Supply","Servicii=Service"
    
    # Onsite Field -Tipul contractului
    # Onsite Comment -None

    try:
        notice_data.contract_type_actual = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > strong:nth-child(7)').text
        if "Servicii" in notice_data.contract_type_actual:
            notice_data.notice_contract_type="Service"
        elif "Lucrari" in notice_data.contract_type_actual:
            notice_data.notice_contract_type='Works'
        elif "Furnizare" in notice_data.contract_type_actual:
            notice_data.notice_contract_type='Supply'
    except Exception as e:
        logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -CPV
    # Onsite Comment -None
    
    try:              
        cpvs_data = cpvs()
        cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > strong:nth-child(5)').text
        cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]  
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpvs_data.cpv_code+','
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    notice_data.class_at_source = 'CPV'

    try:
        notice_url_click = WebDriverWait(tender_html_element,150).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.col-md-9.padding-right-0 > h2 > a')))
        page_main.execute_script("arguments[0].click();",notice_url_click)
        time.sleep(10)
        notice_data.notice_url = page_main.current_url
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info(notice_data.notice_url)
    
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#container-sizing').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.notice_no = notice_no
    except:
        try:
            notice_no = notice_data.notice_url
            notice_data.notice_no = re.findall('\d{9}',notice_no)[0]
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Descriere succinta
    # Onsite Comment -None

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Descriere succinta")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    try:
        notice_data.related_tender_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Numar de referinta:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Valoarea totala estimata:
    # Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197356"

    try:
        est_amount_data = page_main.find_element(By.CSS_SELECTOR, '#container-sizing').text.split("II.1.5) Valoarea totala estimata:")[1].split("II.1.6) Informatii privind loturile:")[0].strip()
        if "si" in est_amount_data:
            est_amount = est_amount_data.split("si")[1]
            est_amount = re.sub("[^\d\.\,]","",est_amount)
        else:
            est_amount = est_amount_data
            est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','.').replace('.','').strip()) 
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Adresa profilului cumparatorului
    # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa profilului cumparatorului")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    cpv_data1 =page_main.find_element(By.CSS_SELECTOR, '#container-sizing').text
    try:
        cpv1  =fn.get_string_between(cpv_data1, 'II.2.2) Coduri CPV secundare:', 'II.2.3) Locul de executare:')
        cpv_regex1 = re.compile(r'\d{8}')
        lot_cpvs_dataa1 = cpv_regex1.findall(cpv1)
        for cpv in lot_cpvs_dataa1:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            notice_data.cpv_at_source += cpv
            notice_data.cpv_at_source += ','
        notice_data.cpv_at_source = notice_data.cpv_at_source.rstrip(',')
    except:
        pass
    
    # Onsite Field -if it is given as " financed by European Union funds: No  " than pass the "None " ------else if is written " financed by European Union funds: YES  " than pass the "Funding agency" name as "European Agency
    # Onsite Comment -None

    try:
        source_of_funds = page_main.find_element(By.XPATH, '//*[contains(text()," Informatii despre fondurile Uniunii Europene")]//following::span[2]').text
        source_of_funds = GoogleTranslator(source='ro', target='en').translate(source_of_funds)
        if 'Yes' in source_of_funds:
            notice_data.source_of_funds = 'European Agency'
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 1344862
            notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))

    try:              
        customer_details_data = customer_details()
    # Onsite Field -Tara
    # Onsite Comment -None

        customer_details_data.org_country = "RO"
        
        customer_details_data.org_language = 'RO'
    # Onsite Field -Autoritate contractanta
    # Onsite Comment -take data which is after "Autoritate contractanta"

        customer_details_data.org_name = org_name

    # Onsite Field -Denumire si adrese
    # Onsite Comment -Note: splite data between  Adresa till E-mail

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split("Adresa:")[1].split("E-mail:")[0].strip()
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
    # Onsite Comment -Note:Splite after Fax

        try:
            org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split("Fax:")[1].split("Adresa Internet (URL):")[0].strip()
            if "-" in org_fax:
                pass
            else:
                customer_details_data.org_fax = org_fax
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
    # Onsite Comment -ref url - "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197354"

        try:
            postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod postal:")]//following::span[1]').text
            if "-" in postal_code:
                pass
            else:
                customer_details_data.postal_code = postal_code
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Cod NUTS
    # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split("Cod NUTS:")[1].split("Localitate:")[0].strip()
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -Adresa web a sediului principal al autoritatii/entitatii contractante(URL)
    # Onsite Comment -None

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa web a sediului principal al autoritatii/entitatii contractante(URL)")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass


    # Onsite Field -Activitate principala
    # Onsite Comment -None

        try:
            customer_details_data.customer_main_activity = page_main.find_element(By.XPATH, '//*[contains(text(),"Activitate principala")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

    # Onsite Field -Tipul autoritatii contractante
    # Onsite Comment -None

        try:
            customer_details_data.type_of_authority_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Tipul autoritatii contractante")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
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

        tender_custom_tag_company_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod fiscal")]//following::span[1]').text
        custom_tags_data.tender_custom_tag_company_id = (tender_custom_tag_company_id)

        custom_tags_data.custom_tags_cleanup()
        notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass

# Onsite Field -None
# Onsite Comment -ref url "https://www.e-licitatie.ro/pub/notices/simplified-notice/v2/view/100197353"
    
#Onsite Field -VEZI PROCEDURA
# Onsite Comment -take lots data by clicking on "VEZI PROCEDURA" from tender_html_element >>>> click on "Lista de loturi" from page_detail  ...........ref url "https://www.e-licitatie.ro/pub/procedure/view/100250427/"
    
    try:
        range_lot=page_main.find_element(By.CSS_SELECTOR, 'div.row.margin-top-10.text-align-center > ul > li:nth-child(3) > a').text.split("of")[1].strip()
        lot=int(range_lot)
        time.sleep(10)
        lot_number=1
        for page_no in range(1,lot+1):                                                                          
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div:nth-child(9) > div > div > div.c-lots-list__items > div'))).text
            rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div:nth-child(9) > div > div > div.c-lots-list__items > div')))
            length = len(rows)
            
            for records in range(0,length):
                single_record = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div:nth-child(9) > div > div > div.c-lots-list__items > div')))[records]
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                
                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__header.row > div > h4').text
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
                try:
                    lot_click = single_record.find_element(By.CSS_SELECTOR, ' a').click()
                    time.sleep(10)
                except:
                    pass
                
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__header.row > div > h4').text.split(".")[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_grossbudget_lc_data = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__content > div > div.col-xs-7ss > div.c-lots-list__item__value > span').text
                    if "-" in lot_grossbudget_lc_data:
                        lot_grossbudget_lc = lot_grossbudget_lc_data.split("-")[1]
                        lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                        lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                    else:
                        lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc_data)
                        lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_cpvs_data = lot_cpvs()

                    # Onsite Field -CPV code
                    # Onsite Comment -None

                    lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__content > div > div.col-xs-5 > div > div.c-lots-list__item__value.truncate.ng-binding').text
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
                
                try:
                    lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Codul NUTS:")]//following::span[1]').text.strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Descrierea achizitiei publice:")]//following::span[1]').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Durata in luni:")]//following::span[1]').text.strip()
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass
                
                try:              
                    for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.k-kendo-modal.k-window-content.k-content > div > div > div:nth-child(5) > div > div > div:nth-child(3) > div > div')[1:]:
                        lot_criteria_data = lot_criteria()
                    # Onsite Field -Criterii de atribuire >>>> DESCRIERE
                    # Onsite Comment -None

                        lot_criteria_data.lot_criteria_title =single_record.find_element(By.CSS_SELECTOR, 'div > div.col-md-4').text
                        if 'Pretul' in lot_criteria_title.lower():
                            lot_criteria_data.lot_criteria_title = 'Pretul'
                        else:
                            lot_criteria_data.lot_criteria_title = lot_criteria_title

                    # Onsite Field -Criterii de atribuire >> PONDERE
                    # Onsite Comment -or use following path "//*[contains(text(),"Pondere")]//following::div/div/div[3]/div[1]"

                        lot_criteria_weight  = single_record.find_element(By.CSS_SELECTOR, ' div > div:nth-child(1) > div.col-md-3 > div:nth-child(1)').text.split("%")[0].strip()
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                        
                        if "Pretul" in lot_criteria_data.lot_criteria_title:
                            lot_criteria_data.lot_is_price_related = True

                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__)) 
                    pass
                try:
                    lot_click_back = page_main.find_element(By.XPATH, "//a[@class='k-window-action k-link']//following::span[72]").click()
                    time.sleep(5)
                except:
                    pass
                
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
                
            if lot == page_no:
                break
            next_lot_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.row.margin-top-10.text-align-center > ul > li:nth-child(4) > a"))).click()
            time.sleep(10)
            try:
                scheight = 4.9
                while scheight >.1:
                    page_details.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
                    break
                time.sleep(2)
            except:
                pass
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div:nth-child(9) > div > div > div.c-lots-list__items > div'),page_check))
    except:
        try:
            lot_number=1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div:nth-child(9) > div > div > div.c-lots-list__items > div'):
                data = single_record.text
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__header.row > div > h4').text
                lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
                
                try:
                    lot_click = single_record.find_element(By.CSS_SELECTOR, ' a').click()
                    time.sleep(10)
                except:
                    pass
                
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__header.row > div > h4').text.split(".")[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass
                
                # Onsite Field -VALOARE ESTIMATA LOT
    #         # Onsite Comment -None

                try:
                    lot_grossbudget_lc_data = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__content > div > div.col-xs-7ss > div.c-lots-list__item__value > span').text
                    if "-" in lot_grossbudget_lc_data:
                        lot_grossbudget_lc = lot_grossbudget_lc_data.split("-")[1]
                        lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                        lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                    else:
                        lot_grossbudget_lc = lot_grossbudget_lc_data
                        lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                        lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                except Exception as e:
                    logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_cpvs_data = lot_cpvs()

                    # Onsite Field -CPV code
                    # Onsite Comment -None

                    lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'div > div.c-lots-list__item__content > div > div.col-xs-5 > div > div.c-lots-list__item__value.truncate.ng-binding').text
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
                
                try:
                    lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Codul NUTS:")]//following::span[1]').text.strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Descrierea achizitiei publice:")]//following::span[1]').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_details_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Durata in luni:")]//following::span[1]').text.strip()
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass
                
                try:              
                    for single_record in page_main.find_elements(By.CSS_SELECTOR, 'div.k-kendo-modal.k-window-content.k-content > div > div > div:nth-child(5) > div > div > div:nth-child(3) > div > div')[1:]:
                        lot_criteria_data = lot_criteria()
                    # Onsite Field -Criterii de atribuire >>>> DESCRIERE
                    # Onsite Comment -None

                        lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-md-4').text
                        if 'Pretul' in lot_criteria_title.lower():
                            lot_criteria_data.lot_criteria_title = 'Pretul'
                        else:
                            lot_criteria_data.lot_criteria_title = lot_criteria_title

                    # Onsite Field -Criterii de atribuire >> PONDERE
                    # Onsite Comment -or use following path "//*[contains(text(),"Pondere")]//following::div/div/div[3]/div[1]"

                        lot_criteria_weight  = single_record.find_element(By.CSS_SELECTOR, ' div > div:nth-child(1) > div.col-md-3 > div:nth-child(1)').text.split("%")[0].strip()
                        lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                        
                        if "Pretul" in lot_criteria_data.lot_criteria_title:
                            lot_criteria_data.lot_is_price_related = True

                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__)) 
                    pass
                
                lot_click_back = page_main.find_element(By.XPATH, "//a[@class='k-window-action k-link']//following::span[72]").click()
                time.sleep(5)

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass
        
    try:
        lot_data1 =  page_main.find_element(By.CSS_SELECTOR, '#container-sizing').text
        if "VALOARE ESTIMATA " not in lot_data1:
            lot_details_data = lot_details()
            lot_details_data.lot_number= 1
            lot_details_data.contract_type = notice_data.notice_contract_type
            lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

            lot_details_data.lot_title = notice_data.local_title
            notice_data.is_lot_default = True
            lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

            try:
                lot_details_data.lot_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Codul NUTS:")]//following::span[1]').text.strip()
            except Exception as e:
                logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                pass

            try:
                lot_details_data.lot_description = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.4) Descrierea achizitiei publice:")]//following::span[1]').text
                lot_details_data.lot_description = lot_details_data.lot_description[:4000]
                lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"Durata in zile:")]//following::span[1]').text.strip()
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass

            try:
                lot_cpvs_data = lot_cpvs()

                # Onsite Field -CPV code
                # Onsite Comment -None
                lot_cpv_code = fn.get_string_between(lot_data1, 'II.2.2) Coduri CPV secundare:', 'II.2.3) Locul de executare:')
                cpv_regex = re.compile(r'\d{8}')
                lot_cpvs_dataa = cpv_regex.findall(lot_cpv_code)
                for cpv in lot_cpvs_dataa:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = cpv
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
            
            try:
                cpv = fn.get_string_between(lot_data1, 'II.2.2) Coduri CPV secundare:', 'II.2.3) Locul de executare:')
                cpv_regex = re.compile(r'\d{8}')
                lot_cpvs_dataa = cpv_regex.findall(cpv)
                lot_cpv_at_source = ''
                for cpv in lot_cpvs_dataa:
                    lot_cpv_at_source += cpv
                    lot_cpv_at_source += ','
                lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')
            except:
                pass
            
            try:              
                for single_record in page_main.find_elements(By.CSS_SELECTOR, '#section-2 > div.widget-body > ng-transclude > div:nth-child(9) > div > div:nth-child(4) > div > div > div:nth-child(3) > div > div ')[1:]:
                    lot_criteria_data = lot_criteria()
                # Onsite Field -Criterii de atribuire >>>> DESCRIERE
                # Onsite Comment -None

                    lot_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'div > div.col-md-4').text
                    if 'Pretul' in lot_criteria_title.lower():
                        lot_criteria_data.lot_criteria_title = 'Pretul'
                    else:
                        lot_criteria_data.lot_criteria_title = lot_criteria_title
                    
                # Onsite Field -Criterii de atribuire >> PONDERE
                # Onsite Comment -or use following path "//*[contains(text(),"Pondere")]//following::div/div/div[3]/div[1]"

                    lot_criteria_weight  = single_record.find_element(By.CSS_SELECTOR, ' div > div:nth-child(1) > div.col-md-3 > div:nth-child(1)').text.split("%")[0].strip()
                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_weight)
                    
                    if "Pretul" in lot_criteria_data.lot_criteria_title:
                        lot_criteria_data.lot_is_price_related = True

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
            except Exception as e:
                logging.info("Exception in lot_criteria: {}".format(type(e).__name__)) 
                pass
            
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except:
        pass
            
    
    try:              
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#container-sizing > div.c-sticky-header-content.c-df-notice.ng-scope > div:nth-child(3) > div > div.widget-body > ng-transclude > div > div > div  > strong')[:-1]:
            attachments_data = attachments()

            attachments_data.file_name = single_record.text
            time.sleep(5)
        # Onsite Field -None
        # Onsite Comment -click on "   Lista de fisiere care compun documentatia de atribuire" for details

            external_url = single_record.find_element(By.CSS_SELECTOR, 'a').click()
            time.sleep(10)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        # Onsite Field -None
        # Onsite Comment -click on "   Lista de fisiere care compun documentatia de atribuire" for details

            try:
                file_type = single_record.text
                if 'pdf' in file_type:
                    attachments_data.file_type = 'pdf'
                elif 'docx' in file_type:
                    attachments_data.file_type = 'docx'
                elif 'doc' in file_type:
                    attachments_data.file_type = 'doc'
                elif 'xlsx' in file_type:
                    attachments_data.file_type = 'xlsx'         
                else:
                    pass
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

        # Onsite Field -None
        # Onsite Comment -click on "   Lista de fisiere care compun documentatia de atribuire" for details

    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    back = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.ng-isolate-scope.btn.btn-default.carbon.shutter-out-vertical")))
    page_main.execute_script("arguments[0].click();",back)
    time.sleep(3)
    
    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div')))

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.notice_deadline) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = Doc_Download.page_details
action = ActionChains(page_main)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.e-licitatie.ro/pub/notices/contract-notices/list/0/0"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        try:
            status_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="container-sizing"]/div[7]/div[2]/ng-transclude/div[1]/div[2]/div[4]/div/div[2]/div[1]/span/span/span'))).click()    
            time.sleep(5)

            action = ActionChains(page_main)

            action.send_keys(Keys.ENTER) 
            time.sleep(5)

            action.perform()
        except:
            pass
        
        try:
            status_click_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="container-sizing"]/div[7]/div[2]/ng-transclude/div[1]/div[2]/div[4]/div/div[1]/div[1]/span/span/span/span')))
            page_main.execute_script("arguments[0].click();",status_click_2)
            time.sleep(5)

            action = ActionChains(page_main)

            action.send_keys(Keys.ARROW_LEFT)
            time.sleep(2)

            action.send_keys(Keys.ENTER) 
            time.sleep(2)

            action.perform()
        except:
            pass
    
        search = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="THE-SEARCH-BUTTON"]')))
        page_main.execute_script("arguments[0].click();",search)
        time.sleep(2)
        
        try:
            for page_no in range(1,10):#10
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[9]/div[2]/div')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="container-sizing"]/div[9]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(6) > div > ul > li:nth-child(5) > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="container-sizing"]/div[9]/div[2]/div'),page_check))
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
    
