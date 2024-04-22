from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ro_elicitatie_ca"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ro_elicitatie_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

# Urban VPN(Romania)

    notice_data.script_name = 'ro_elicitatie_ca'
 
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RO'
    notice_data.performance_country.append(performance_country_data)
  
    notice_data.currency = 'RON'
  
    notice_data.main_language = 'RO'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 7
    
    notice_data.class_at_source = 'CPV'
    
    try:
        org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 div > div:nth-child(2) > div').text.split("-")[1]
    except:
        pass
    # Onsite Field -NUMAR ANUNT DATA PUBLICARE
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-1.margin-top-10 > div:nth-child(1) > strong').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -NUMAR ANUNT DATA PUBLICARE
    # Onsite Comment -None

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
    
    # Onsite Field -Tipul contractului
    # Onsite Comment -Note:Repleace following keywords with given keywords("Lucrari=Works","Furnizare=Supply","Servicii=Service")

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > strong:nth-child(7)').text
        notice_data.contract_type_actual = notice_contract_type 
        if "Lucrari" in notice_contract_type:
             notice_data.notice_contract_type='Works'
        elif "Furnizare" in notice_contract_type:
            notice_data.notice_contract_type='Supply'
        elif "Servicii" in notice_contract_type:
            notice_data.notice_contract_type='Service'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Modalitatea de atribuire
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9 div > div:nth-child(2) > strong:nth-child(2)').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -DENUMIRE CONTRACT
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.col-md-9.padding-right-0 > h2').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:              
        cpvs_data = cpvs()
        cpv_code = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > strong:nth-child(5)').text
        cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0]        
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -CPV
    # Onsite Comment -None

    try:
        cpv_at_source = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > strong:nth-child(5)').text
        notice_data.cpv_at_source = re.findall('\d{8}',cpv_at_source)[0]
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass
        
    page_detail_click = WebDriverWait(tender_html_element, 200).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.col-md-9.padding-right-0 > h2 > a')))
    page_main.execute_script("arguments[0].click();",page_detail_click)
    time.sleep(80)
    notice_data.notice_url = page_main.current_url
    logging.info(notice_data.notice_url)
    
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, '#container-sizing').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
     
#     # Onsite Field -Descriere succinta
#     # Onsite Comment -None

    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Descriere succinta")]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='ro', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
   

#     # Onsite Field -II.2.7) Durata contractului, concesiunii, a acordului-cadru sau a sistemului dinamic de achizitii
#     # Onsite Comment -None
#     # reference_url=https://www.e-licitatie.ro/pub/notices/ca-notices/view-c/100408569


    try:
        notice_data.contract_duration = page_main.find_element(By.XPATH, '//*[contains(text(),"II.2.7)")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_main.find_element(By.XPATH, '//*[contains(text(),"Data expedierii prezentului anunt")]//following::span[1]').text
        dispatch_date1=re.findall('\d+ \w{3}',dispatch_date)[0]
        dispatch_date_year=re.findall('\d{4}',dispatch_date)[0]
        dispatch_date3=dispatch_date1+' '+dispatch_date_year
        notice_data.dispatch_date =datetime.strptime(dispatch_date3,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Valoarea totala a achizitiei (fara TVA)
#     # Onsite Comment -None

    try:
        netbudgetlc = page_main.find_element(By.XPATH, '//*[contains(text(),"Valoarea totala a achizitiei (fara TVA)")]//following::span[4]').text
        netbudgetlc = re.sub("[^\d\.\,]","",netbudgetlc)
        netbudgetlc =netbudgetlc.replace('.','')
        notice_data.netbudgetlc = float(netbudgetlc.replace(',','.').strip()) 
        notice_data.est_amount = notice_data.netbudgetlc
        notice_data.netbudgeteuro =notice_data.est_amount
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Adresa profilului cumparatorului (URL)
#     # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa profilului cumparatorului (URL)")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    try:              
        custom_tags_data = custom_tags()
        # Onsite Field -Cod de identitate fiscala
        # Onsite Comment -None

        custom_tags_data.tender_custom_tag_company_id = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod de identitate fiscala")]//following::span[1]').text.replace("RO","").strip()

        custom_tags_data.custom_tags_cleanup()
        notice_data.custom_tags.append(custom_tags_data)
    except Exception as e:
        logging.info("Exception in custom_tags: {}".format(type(e).__name__)) 
        pass
 
    try:                                          
        for single_record in page_main.find_elements(By.CSS_SELECTOR, '#section-2-2-new_0 > div.widget-body.c-section__content > div:nth-child(7) > div > div:nth-child(2) > div > div')[1:]:
            tender_criteria_data = tender_criteria()
        # Onsite Field -Criterii de atribuire >> DESCRIERE
        # Onsite Comment -None

            tender_criteria_title = single_record.text.split("\n")[0].strip()
            tender_criteria_title = GoogleTranslator(source='ro', target='en').translate(tender_criteria_title)
            
            if 'technique' in tender_criteria_title.lower():
                tender_criteria_data.tender_criteria_title = 'technique'
            elif 'price' in tender_criteria_title.lower():
                tender_criteria_data.tender_criteria_title = 'price'
        
        # Onsite Field -Criterii de atribuire >> PONDERE
        # Onsite Comment -None

            tender_criteria_weight = single_record.text.split("\n")[-1]
            tender_criteria_data.tender_criteria_weight=int(tender_criteria_weight.split("%")[0].strip())
            
            if "price" in tender_criteria_data.tender_criteria_title:
                tender_criteria_data.tender_is_price_related = True
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None
# # reference_url=https://www.e-licitatie.ro/pub/notices/ca-notices/view-c/100408684

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_language = 'RO'
        customer_details_data.org_country = "RO"
#         # Onsite Field -Autoritate contractanta
#         # Onsite Comment -None

        customer_details_data.org_name = org_name
    
#         # Onsite Field -Denumire si adrese
#         # Onsite Comment -Note: splite between  Adresa to E-mail

        try:
            customer_details_data.org_address = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split("Adresa:")[1].split("E-mail:")[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -E-mail
#         # Onsite Comment -None

        try:
            org_email = page_main.find_element(By.XPATH, '//*[contains(text(),"E-mail:")]//following::span[1]').text
            customer_details_data.org_email  = re.findall(r'[\w\.-]+@[\w\.-]+', org_email)[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Telefon
#         # Onsite Comment -None

        try:
            customer_details_data.org_phone = page_main.find_element(By.XPATH, '//*[contains(text(),"Telefon:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Denumire si adrese
#         # Onsite Comment -Note:Splite after Fax

        try:
            customer_details_data.org_fax = page_main.find_element(By.XPATH, '//*[contains(text(),"Denumire si adrese")]//following::div[1]').text.split("Fax:")[1].split(" Persoana de contact")[0]
        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Localitate
#         # Onsite Comment -None

        try:
            customer_details_data.org_city = page_main.find_element(By.XPATH, '//*[contains(text(),"Localitate:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Cod Postal
#         # Onsite Comment -None

        try:
            customer_details_data.postal_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod Postal:")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Cod NUTS
#         # Onsite Comment -None

        try:
            customer_details_data.customer_nuts = page_main.find_element(By.XPATH, '//*[contains(text(),"Cod NUTS")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Adresa web a sediului principal al autoritatii/entitatii contractante(URL)
#         # Onsite Comment -None

        try:
            customer_details_data.org_website = page_main.find_element(By.XPATH, '//*[contains(text(),"Adresa web a sediului principal al autoritatii/entitatii contractante(URL)")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Persoana de contact
#         # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_main.find_element(By.XPATH, '//*[contains(text(),"Persoana de contact")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Activitate principala
#         # Onsite Comment -None

        try:
            customer_details_data.customer_main_activity = page_main.find_element(By.XPATH, '//*[contains(text(),"Activitate principala")]//following::span[1]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

#         # Onsite Field -Tipul autoritatii contractante
#         # Onsite Comment -None

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
    
# # Onsite Field -[VEZI PROCEDURA]  #container-sizing > div.u-items-list > div.u-items-list__content > div:nth-child(1) > div > div > div.col-md-2 > div.u-items-list__item__value.title-entity.ng-scope
# # Onsite Comment -Note:take lots by clicking on "[VEZI PROCEDURA]" and clicking on "Lista de loturi" dropdownlist in tender_html_element
# # reference_url=https://www.e-licitatie.ro/pub/procedure/view/100178041/
    try:
        range_lot=page_main.find_element(By.CSS_SELECTOR, 'div.row.margin-top-10.text-align-center > ul > li:nth-child(3) > a').text.split("of")[1].strip()
        lot=int(range_lot)
        lot_number=1
        for page_no in range(1,lot+1):                                                                          
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div:nth-child(4) > div > div:nth-child(3) > div > div > div > div.col-lg-9'))).text
            rows = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div:nth-child(4) > div > div:nth-child(3) > div > div > div > div.col-lg-9')))
            length = len(rows)
            
            for records in range(0,length):
                single_record = WebDriverWait(page_main, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div:nth-child(4) > div > div:nth-child(3) > div > div > div > div.col-lg-9')))[records]
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
    
                try:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div.col-lg-2.ng-scope').get_attribute("k-content")
                    lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' div.col-lg-4').text
                    lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                
                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                except:
                    try:
                        lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(4)').text
                        lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                        lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass

            # reference_url=https://www.e-licitatie.ro/pub/notices/ca-notices/view-c/100407465

                try:
                    award_details_data = award_details()

    #                         # Onsite Field -OFERTANT CASTIGATOR
    #                         # Onsite Comment -None

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div > div').text
        #                         # Onsite Field -NUMAR / DATA
        #                         # Onsite Comment -Note:tack on the date
                    try:
                        award_date = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > div > span').text.split("/")[-1].strip()
                        award_date = GoogleTranslator(source='ro', target='en').translate(award_date)
                        try:
                            award_date1 = re.findall('\w{3}',award_date)[0]
                            award_date_year= re.findall('\d+ \d{4}',award_date)[0]
                            award_date2=award_date1+' '+award_date_year
                            award_details_data.award_date = datetime.strptime(award_date2,'%b %d %Y').strftime('%Y/%m/%d')
                        except:
                            award_date1=re.findall('\d+ \w{3}',award_date)[0]
                            award_date_year=re.findall('\d{4}',award_date)[0]
                            award_date2=award_date1+' '+award_date_year
                            award_details_data.award_date =datetime.strptime(award_date2,'%d %b %Y').strftime('%Y/%m/%d')
                    except:
                        try:
                            award_date = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > span').text.split("/")[-1].strip()
                            award_date = GoogleTranslator(source='ro', target='en').translate(award_date)
                            award_date1 = re.findall('\w{3}',award_date)[0]
                            award_date_year= re.findall('\d+, \d{4}',award_date)[0]
                            award_date2=award_date1+' '+award_date_year
                            award_details_data.award_date = datetime.strptime(award_date2,'%b %d %Y').strftime('%Y/%m/%d')
                        except Exception as e:
                            logging.info("Exception in award_date: {}".format(type(e).__name__))
                            pass
                                                                                                              
    #                         # Onsite Field -VALOARE CONTRACT
    #                         # Onsite Comment -None
                    try:  
                        grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > div').text
                        if "-" in grossawardvaluelc:
                            grossawardvaluelc1=grossawardvaluelc.split("-")[-1]
                            grossawardvaluelc1 = re.sub("[^\d\.\,]","",grossawardvaluelc1)
                            grossawardvaluelc1=grossawardvaluelc1.replace('.','')
                            award_details_data.grossawardvaluelc = float(grossawardvaluelc1.replace(',','.').strip())
                        else:
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            grossawardvaluelc =grossawardvaluelc.replace('.','')
                            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
                    except:
                        try:  
                            grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(4) > div').text
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            grossawardvaluelc =grossawardvaluelc.replace('.','')
                            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
                        except Exception as e:
                            logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                            pass
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass
            
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
                
            if lot == page_no:
                break
            next_lot_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div.row.margin-top-10.text-align-center > ul > li:nth-child(4) > a"))).click()
            time.sleep(10)
            WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div:nth-child(4) > div > div:nth-child(3) > div > div > div > div.col-lg-9'),page_check))
    except:
        try:
            lot_number=1
            for single_record in page_main.find_elements(By.CSS_SELECTOR, ' div:nth-child(4) > div > div:nth-child(3) > div > div > div > div.col-lg-9'):
                lot_details_data = lot_details()
                lot_details_data.lot_number=lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

                try:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div.col-lg-2.ng-scope').get_attribute("k-content")
                    lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, ' div.col-lg-4').text
                    lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                    
                # Onsite Field -VALOARE ESTIMATA LOT
    #         # Onsite Comment -None

                try:
                    lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                    lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                except:
                    try:
                        lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(4)').text
                        lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc)
                        lot_grossbudget_lc =lot_grossbudget_lc.replace('.','')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','.').strip())
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass

                try:
                    award_details_data = award_details()

    #                         # Onsite Field -OFERTANT CASTIGATOR
    #                         # Onsite Comment -None

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(3) > div > div').text
        #                         # Onsite Field -NUMAR / DATA
        #                         # Onsite Comment -Note:tack on the date
                    try:
                        award_date = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > span').text.split("/")[-1].strip()
                        award_date = GoogleTranslator(source='ro', target='en').translate(award_date)
                        try:
                            award_date1 = re.findall('\w{3}',award_date)[0]
                            award_date_year= re.findall('\d+ \d{4}',award_date)[0]
                            award_date2=award_date1+' '+award_date_year
                            award_details_data.award_date = datetime.strptime(award_date2,'%b %d %Y').strftime('%Y/%m/%d')
                        except:
                            award_date1=re.findall('\d+ \w{3}',award_date)[0]
                            award_date_year=re.findall('\d{4}',award_date)[0]
                            award_date2=award_date1+' '+award_date_year
                            award_details_data.award_date =datetime.strptime(award_date2,'%d %b %Y').strftime('%Y/%m/%d')
                    except:
                        try:
                            award_date = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div > span').text.split("/")[-1].strip()
                            award_date = GoogleTranslator(source='ro', target='en').translate(award_date)
                            award_date1 = re.findall('\w{3}',award_date)[0]
                            award_date_year= re.findall('\d+, \d{4}',award_date)[0]
                            award_date2=award_date1+' '+award_date_year
                            award_details_data.award_date = datetime.strptime(award_date2,'%b %d %Y').strftime('%Y/%m/%d')
                        except Exception as e:
                            logging.info("Exception in award_date: {}".format(type(e).__name__))
                            pass
                    
                    
    #                         # Onsite Field -VALOARE CONTRACT
    #                         # Onsite Comment -None
                    try:  
                        grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div').text
                        if "-" in grossawardvaluelc:
                            grossawardvaluelc1=grossawardvaluelc.split("-")[-1]
                            grossawardvaluelc1 = re.sub("[^\d\.\,]","",grossawardvaluelc1)
                            grossawardvaluelc1=grossawardvaluelc1.replace('.','')
                            award_details_data.grossawardvaluelc = float(grossawardvaluelc1.replace(',','.').strip())
                        else:
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            grossawardvaluelc =grossawardvaluelc.replace('.','')
                            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
                    except:
                        try:  
                            grossawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(4) > div').text
                            grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                            grossawardvaluelc =grossawardvaluelc.replace('.','')
                            award_details_data.grossawardvaluelc = float(grossawardvaluelc.replace(',','.').strip())
                        except Exception as e:
                            logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                            pass
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__))
            pass

    try:
        back2 = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button.ng-isolate-scope.btn.btn-default.carbon.shutter-out-vertical")))
        page_main.execute_script("arguments[0].click();",back2)
        time.sleep(5)
    except Exception as e:
        logging.info("Exception in click: {}".format(type(e).__name__))
        pass

    WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.col-md-1.margin-top-10 > div:nth-child(2) > span')))
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
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
    urls = ["https://www.e-licitatie.ro/pub/notices/contract-award-notices/list/3/1"] 
    for url in urls: 
        fn.load_page(page_main, url, 200)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,20):                                                                     
                page_check = WebDriverWait(page_main, 200).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.u-items-list__content > div'))).text
                rows = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.u-items-list__content > div')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 100).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.u-items-list__content > div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"div:nth-child(6) > div > ul > li:nth-child(5) > a")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    time.sleep(5)
                    WebDriverWait(page_main, 100).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'div.u-items-list__content > div'),page_check))
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
