from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fi_hanki_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fi_hanki_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -the following two formats have been identified 
#format 1  
#https://www.hankintailmoitukset.fi/fi/public/procurement/92953/notice/136810/overview

#format 2
#https://www.hankintailmoitukset.fi/fi/public/procedure/28/enotice/86/ 

    notice_data.script_name = 'fi_hanki_spn'
    notice_data.main_language = 'FI'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FI'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -if document_type_description have following keywords "Vapaaehtoista ennakkoavoimuutta (ex ante) koskeva ilmoitus ,POST-ANNOUNCEMENT,SUBSEQUENT ANNOUNCEMENT,Post notification" then do not take tender in spn skip the records
    notice_data.notice_type = 4
    
    notice_data.class_at_source = "CPV"
    
    # Onsite Field -Ilmoitustyyppi
    # Onsite Comment -if 'Kansallinen hankintailmoitus'/ 'Kansallinen pienhankinta' keyword is present then take procurement method "0" otherwise take  "2"
    
    # Onsite Field -Ilmoitustyyppi
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
        
        if 'Vapaaehtoista ennakkoavoimuutta (ex ante) koskeva ilmoitus - Puolustus ja turvallisuus' in notice_data.document_type_description:
            return
        if 'JÄLKI-ILMOITUS' in notice_data.document_type_description or 'Jälki-ilmoitus - SOTE ja erityiset palvelut' in notice_data.document_type_description:
            return
        if 'Jälki-ilmoitus' in notice_data.document_type_description or 'Sopimusmuutos' in notice_data.document_type_description:
            return
        
        if 'Kansallinen hankintailmoitus' in notice_data.document_type_description or 'Kansallinen pienhankinta' in notice_data.document_type_description:
            notice_data.procurement_method = 0
        else:
            notice_data.procurement_method = 2
    except Exception as e:
        logging.info("Exception in procurement_method: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nimi
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Julkaistu
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
    
    # Onsite Field -Määräaika
    # Onsite Comment -take notice_deadline for notice_type 4

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Nimi
    # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    #format 1
    # Onsite Field -None
    # Onsite Comment -take all the data from diff tabs ('div.vertbar > ul > li > a')
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    # Onsite Field -Ilmoituksen Hilma-numero
    # Onsite Comment -Both format
    # Onsite Field -Nimi
    # Onsite Comment -if notice_no is not available then take notice_no from notice_url fro both format

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ilmoituksen Hilma-numero")]//following::span[1]').text
    except:
        notice_data.notice_no = notice_data.notice_url.split('notice/')[1].split('/')[0].strip()

    # Onsite Field -Hankinnan lyhyt kuvaus
    # Onsite Comment -format 1
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Lyhyt kuvaus")])[3]//following::div[1]').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan kuvaus")]//following::div[1]').text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        
    # Onsite Field -Hankinnan tyyppi
    # Onsite Comment -format 1
    # Hankinnan tyyppi

    try:
        notice_contract_type = page_details.find_element(By.CSS_SELECTOR, "#main > div").text.split("Hankinnan tyyppi")[1].split("Sopimuksen tyyppi")[1].split("Hankinnan lyhyt kuvaus")[0].strip()
        notice_data.contract_type_actual = notice_contract_type 
        if "Urakat" in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif "Tavarat" in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif "Palvelut" in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif "Services" in notice_contract_type:
            notice_data.notice_contract_type = 'Service'
        elif "Supplies" in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except:
        try:
            notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Pääasiallinen hankintalaji")]//following::div[1]').text
            notice_data.contract_type_actual = notice_contract_type 
            if "Urakat" in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            elif "Tavarat" in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            elif "Palvelut" in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            elif "Services" in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            elif "Supplies" in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            else:
                pass
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Menettelyn luonne
    # Onsite Comment -format 1
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '(//*[contains(text(),"Menettelyn luonne")])[3]//following::div[1]').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fi_hanki_procedure.csv",type_of_procedure)
    except:
        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Menettelyn tyyppi")]//following::div[1]').text
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fi_hanki_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass
    
    # Onsite Field -Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)
    # Onsite Comment -format 1(use this link for ref : 'https://www.hankintailmoitukset.fi/fi/public/procurement/79997/notice/134826/overview')
     # Onsite Field -Arvioitu kokonaisarvo
    # Onsite Comment -format 1(use this link for ref'https://www.hankintailmoitukset.fi/fi/public/procurement/90429/notice/134827/overview')
    
    try:
        est_amount = page_details.find_element(By.XPATH, '(//*[contains(text(),"Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)")])[2]//following::div[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace(' ','').strip())
        notice_data.netbudgeteuro = notice_data.est_amount
        notice_data.netbudgetlc = notice_data.est_amount
    except:
        try:
            est_amount = page_details.find_element(By.XPATH, '(//*[contains(text(),"Arvioitu kokonaisarvo")])[3]//following::div[3]').text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace(' ','').strip())
            notice_data.netbudgeteuro = notice_data.est_amount
            notice_data.netbudgetlc = notice_data.est_amount
            notice_data.grossbudgeteuro = notice_data.est_amount
        except:
            try:
                est_amount = page_details.find_element(By.CSS_SELECTOR, '#main > div').text.split("Arvioitu arvo")[1].split("Puitejärjestelyn enimmäisarvo")[0].split("Hankintanimikkeistö (CPV-koodi)")[0].strip()
                est_amount = re.sub("[^\d\.\,]","",est_amount)
                notice_data.est_amount =float(est_amount.replace(' ','').strip())
                notice_data.netbudgeteuro = notice_data.est_amount
                notice_data.netbudgetlc = notice_data.est_amount
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass
            
    try:
        cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankintanimikkeistö (CPV-koodi)")]//following::div[1]').text
        notice_data.cpv_at_source = re.findall('\d{8}',cpv_at_source)[0]
    except:
        try:
            cpv_at_source = page_details.find_element(By.XPATH, '(//*[contains(text(),"Hankintanimikkeistö")])[3]//following::div[3]').text
            notice_data.cpv_at_source = re.findall('\d{8}',cpv_at_source)[0]
        except:
            pass
    
    try:              
        cpvs_data = cpvs()
        cpvs_data.cpv_code = notice_data.cpv_at_source
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        Ostajaorganisaatio_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//a[contains(text(),"Ostajaorganisaatio")]'))).get_attribute("href")                     
        logging.info(Ostajaorganisaatio_url)
        fn.load_page(page_details1,Ostajaorganisaatio_url,100)
        time.sleep(3)
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_details1, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[2]'))).get_attribute("outerHTML")
    except:
        try:
            notice_data.notice_text += WebDriverWait(page_details1, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div/div/div/div[3]/div'))).get_attribute("outerHTML")
        except:
            pass
        
    # Onsite Field -None
    # Onsite Comment -click on 'Ostajaorganisaatio'tab to get the data
        
    try:
        text_data = page_details1.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div/div[2]').text
    except:
        text_data1 = page_details1.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div/div/div/div/div[3]/div').text
        
    customer_details_data = customer_details()

    try:
        customer_details_data.org_name = page_details1.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div > div > div.notice-public-organisation-contract > div:nth-child(1)').text.split('Virallinen nimi')[1].strip()
    except:
        try:
            customer_details_data.org_name = text_data.split('Organisaation virallinen nimi')[1].split('\n')[1].split('\n')[0].strip()
        except Exception as e:
            logging.info("Exception in org_name: {}".format(type(e).__name__))
            
    
    try:
        customer_details_data.org_city = page_details1.find_element(By.CSS_SELECTOR, '#main > div').text.split("Postitoimipaikka")[1].split("Maa")[0].strip()
    except Exception as e:
        logging.info("Exception in org_city: {}".format(type(e).__name__))

    try:
        customer_details_data.postal_code = page_details1.find_element (By.XPATH, '//*[contains(text(),"Postinumero")]//following::div[1]').text
    except:
        try:
            customer_details_data.postal_code = page_details1.find_element(By.CSS_SELECTOR, '#main > div').text.split('Postinumero')[1].split('TED BT-512: Organisaation postinumero')[1].split("Postitoimipaikka")[0].strip()
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass


# Onsite Field -Ostajaorganisaatio > Postiosoite
# Onsite Comment -format 1  split the data from 'Postiosoite' till 'Aluekoodi'

    try:
        customer_details_data.org_address = text_data1.split('Postiosoite')[1].split('Aluekoodi')[0].strip()
    except:
        try:
            customer_details_data.org_address = text_data.split('Postiosoite')[1].split('Aluekoodi')[0].strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass


# Onsite Field -Ostajaorganisaatio > Sähköpostiosoite
# Onsite Comment -format 1
# Onsite Field -Ostajaorganisaatio > Organisaation yhteyspisteen sähköpostiosoite
# Onsite Comment -format 2

    try:
        customer_details_data.org_email = page_details1.find_element(By.CSS_SELECTOR, ' div:nth-child(3) > div > div:nth-child(2) > div.form-input.col-12.col-lg-6 > p').text
    except:
        try:
            customer_details_data.org_email = text_data.split('Organisaation yhteyspisteen sähköpostiosoite')[1].split('\n')[1].split('\n')[0].strip()
        except:
            try:
                customer_details_data.org_email = text_data1.split('Sähköpostiosoite')[1].split('\n')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass


# Onsite Field -Ostajaorganisaatio > Verkko-osoite
# Onsite Comment -format 1
# Onsite Field -Ostajaorganisaatio > Verkko-osoite
# Onsite Comment -format 2

    try:
        customer_details_data.org_website = text_data1.split('URL')[1].split('\n')[1].split('\n')[0].strip()
    except:
        try:
            customer_details_data.org_website = text_data.split('Verkko-osoite')[1].split('TED BT-505: Organisaation internetosoite')[1].split('Ostajaorganisaation yhteystiedot')[0].strip()
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

# Onsite Field -Ostajaorganisaatio > Aluekoodi
# Onsite Comment -format 1
# Onsite Field -Pääasiallinen toimiala
# Onsite Comment -format 2

    try:
        customer_details_data.customer_nuts = text_data1.split('NUTS-koodi')[1].split('\n')[1].split('\n')[0].strip()
    except Exception as e:
        logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
        pass
    # Pääasiallinen toimiala
     
    try:
        customer_details_data.customer_main_activity = text_data.split('Pääasiallinen toimiala')[1].split('TED BT-10: Viranomaisen toimiala')[1].split('Ostajaryhmän päävastuullinen organisaatio')[0].split("Verolainsäädäntö")[0].split("Työsuojelu ja työehdot")[0].strip()
    except Exception as e:
        logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
        pass
    
    # Ostajaorganisaation tyyppi
    
    try:
        customer_details_data.type_of_authority_code = page_details1.find_element(By.XPATH, '//*[contains(text(),"TED BT-11: Ostajan oikeusstatus")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
        pass
    
    try:
        Osallistuminen_url = page_details.find_element(By.XPATH, '//a[contains(text(),"Osallistuminen")]').get_attribute("href")                     
        logging.info(Osallistuminen_url)
        fn.load_page(page_details2,Osallistuminen_url,180)
        time.sleep(4)
    except:
        pass

    try:
        notice_data.notice_text += WebDriverWait(page_details2, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div/div/div/div[3]/div'))).get_attribute("outerHTML")
    except:
        try:
            notice_data.notice_text += WebDriverWait(page_details2, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[2]'))).get_attribute("outerHTML")
        except:
            pass

# Onsite Field -Osallistuminen > Nimi
# Onsite Comment -format 1   click on 'Osallistuminen'tab to get the data

    try:
        customer_details_data.contact_person = page_details2.find_element(By.XPATH, '(//*[contains(text(),"Nimi")])[3]//following::div[2]').text
    except:
        try: 
            customer_details_data.contact_person = page_details2.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > div > div > div:nth-child(1) > div.form-input.col-12.col-lg-6 > p').text
        except:
            try:
                customer_details_data.contact_person = page_details2.find_element(By.XPATH, ' (//*[contains(text(),"Organisaation puhelinnumero")])[2]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

# Onsite Field -Osallistuminen > Puhelin
# Onsite Comment -format 1   click on 'Osallistuminen'tab to get the data

    try:
        customer_details_data.org_phone = page_details2.find_element(By.XPATH, '(//*[contains(text(),"Puhelin")])[2]//following::div[2]').text
    except:
        try:
            customer_details_data.org_phone = page_details2.find_element(By.XPATH, '//*[contains(text(),"Organisaation yhteyspisteen puhelinnumero")]//following::div[1]').text
        except:
            try:
                customer_details_data.org_phone = page_details2.find_element(By.XPATH, ' (//*[contains(text(),"Organisaation puhelinnumero")])[2]//following::div[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
            
    customer_details_data.org_country = 'FI'
    customer_details_data.org_language = 'FI'
    customer_details_data.customer_details_cleanup()
    notice_data.customer_details.append(customer_details_data)

    try:
        Tarkemmat_url = page_details.find_element(By.XPATH, '//a[contains(text(),"Tarkemmat tiedot")]').get_attribute("href")                     
        fn.load_page(page_details3,Tarkemmat_url,100)
    except:
        pass
    
    try:
        contract_duration = page_details3.find_element(By.CSS_SELECTOR, '#main > div').text.split("Sopimuksen kesto")[1].split("\n")[:3]
        contract_duration=" ".join(contract_duration)
        if "MENETTELYN LUONNE" in contract_duration:
            notice_data.contract_duration = contract_duration.replace("MENETTELYN LUONNE","")
        else:
            notice_data.contract_duration = contract_duration.strip()
    except:
        pass
    
    try:
        notice_data.notice_text += page_details3.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div/div/div/div/div[3]/div').get_attribute("outerHTML")
    except:
        try:
            notice_data.notice_text += page_details3.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div/div[2]').get_attribute("outerHTML")
        except:
            pass
        
    try:              
        for single_record in page_details3.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > div >div.notice-public-lot > div:nth-child(7) > div > div > div.selection-cell.flex-grow-1 > div > div')[1:2]:
            text_weight = single_record.text
            if 'Hinta' in text_weight and '%' in text_weight:
                tender_criteria_data = tender_criteria()
            # Onsite Field -Tarjousten valintaperusteet
            # Onsite Comment -format 1

                tender_criteria_data.tender_criteria_title = single_record.text.split('\n')[0].strip()
                
            # Onsite Field -Tarjousten valintaperusteet
            # Onsite Comment -format 1
                tender_criteria_weight = single_record.text.split('\n')[1].split('%')[0].strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except:
        try:
            tender_criteria_data = tender_criteria()
            tender_criteria_data.tender_criteria_title = page_details3.find_element(By.CSS_SELECTOR, '#main > div').text.split("Tarjousten vertailuperusteet")[1].split("Sopimuksen kesto")[0].strip()
            tender_criteria_weight = tender_criteria_data.tender_criteria_title
            tender_criteria_weight = tender_criteria_weight.replace("\n", " ")
            tender_criteria_weight =re.findall('\d{3}',tender_criteria_weight)[0]
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass

# Onsite Field -OSIA KOSKEVAT TIEDOT
# Onsite Comment -ref ('https://www.hankintailmoitukset.fi/fi/public/procurement/91883/notice/135037/details')

    try:              
        lot_number = 1
        for single_record in page_details3.find_elements(By.CSS_SELECTOR, '#main > div > div.container > div > div > div > div > div:nth-child(3) > div > div')[3:]:
            lot =  single_record.text
#             lot_details_data = lot_details()
#             lot_details_data.lot_number = lot_number

            if 'OSA' in lot and "Osan nimi" in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.contract_type = notice_data.notice_contract_type
                lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                
                
    # #         # Onsite Field -OSIA KOSKEVAT TIEDOT
    # #         # Onsite Comment -split lot_actual_no from the given selector for ex.: from "OSA 1 - TILATYYPPI 1: YHDEN SISÄÄNKÄYNNIN SISÄTILA, PIRKKOLAN JÄÄHALLI" take only "OSA 1"

                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, '.notice-public-lot > h2').text.split('-')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

    #         # Onsite Field -Osan nimi
    #         # Onsite Comment -None

                lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(2) > div.value-row-value.col-12.col-sm-8 > div').text
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

    #             # Onsite Field -Kuvaus hankinnasta
    #             # Onsite Comment -None

                try:
                    lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > div.value-row-value.col-12.col-sm-8 > div').text
                    lot_details_data.lot_description_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description)
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

    #             # Onsite Field -Aluekoodi
    #             # Onsite Comment -None

                try:
                    lot_details_data.lot_nuts = lot.split("NUTS-koodi")[1].split("Suorituspaikan lisätiedot")[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

    #             # Onsite Field -Sopimuksen kesto
    #             # Onsite Comment -None

                try:
                    lot_details_data.contract_duration = lot.split("Sopimuksen kesto")[1].split("OSA ")[0].split("MUUTOKSENHAKUMENETTELY")[0].strip()
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass

                
                try:
                    lot_cpv_at_source = lot.split("CPV-lisäkoodi(t)")[1].split("Aluekoodi")[0]
                    lot_details_data.lot_cpv_at_source = re.findall('\d{8}',lot_cpv_at_source)[0]
                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass
                
                try: 
                    lot_cpvs_data = lot_cpvs()

                    # Onsite Field -Lisäkoodit hankintanimikkeistö
                    # Onsite Comment -None
                    lot_cpvs_data.lot_cpv_code = lot_details_data.lot_cpv_at_source
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    lot_criteria_data = lot_criteria()

                    # Onsite Field -Tarjousten valintaperusteet
                    # Onsite Comment -None

                    lot_criteria_data.lot_criteria_title = lot.split("Tarjousten vertailuperusteet")[1].split("Sopimuksen kesto")[0].strip()
                    
                    # Onsite Field -Tarjousten valintaperusteet
                    # Onsite Comment -None

                    lot_criteria_weight = lot_criteria_data.lot_criteria_title
                    lot_criteria_weight = lot_criteria_weight.replace("\n", " ")
                    lot_criteria_data.lot_criteria_weight =re.findall('\d{3}',lot_criteria_weight)[0]
                    lot_criteria_data.lot_criteria_weight = int(lot_criteria_data.lot_criteria_weight)

                    lot_criteria_data.lot_criteria_cleanup()
                    lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass


# Onsite Field -LIITTEET JA LINKIT  # div:nth-child(3) > div > div > div > table > tbody > tr > td > a
# Onsite Comment -(use this link for ref :  'https://www.hankintailmoitukset.fi/fi/public/procurement/91776/notice/134837/overview')

    try:              
        for single_record in page_details.find_elements(By.XPATH, '/html/body/div[1]/main/div/div[2]/div/div/div/div/div[3]/div/div/div/table/tbody/tr/td/a'):
            attachments_data = attachments()
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -take file_type in textform   

            
            attachments_data.file_type = single_record.text.split('.')[-1].strip()
            
        
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -take file_name in textform

            attachments_data.file_name = single_record.text.split('.')[0].strip()
        
        # Onsite Field -LIITTEET JA LINKIT
        # Onsite Comment -None

            attachments_data.external_url = single_record.get_attribute('href')
        
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Pääasiallinen hankintalaji
    # Onsite Comment -Lyhyesti > Pääasiallinen hankintalaji  format 2

    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments)
page_details = fn.init_chrome_driver(arguments) 
page_details1 = fn.init_chrome_driver(arguments)
page_details2 = fn.init_chrome_driver(arguments)
page_details3 = fn.init_chrome_driver(arguments)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.hankintailmoitukset.fi/fi/search'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        for i in range(4):
            Näytä_lisää = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/main/div/div[2]/div[1]/div/div[3]/button')))
            page_main.execute_script("arguments[0].click();",Näytä_lisää)
            time.sleep(3)
        
        try:
            rows = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/div[2]/div[1]/div/table/tbody/tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 160).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[1]/main/div/div[2]/div[1]/div/table/tbody/tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details2.quit()
    page_details3.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
    
