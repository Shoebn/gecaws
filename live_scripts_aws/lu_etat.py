from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "lu_etat"
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
SCRIPT_NAME = "lu_etat"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.script_name = 'lu_etat'
    
    notice_data.main_language = 'FR'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'LU'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.actions > ul.list-unstyled > li:nth-child(1) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url            
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div.date.date-min").text
        publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
        publish_date = publish_date.replace('\n'," ")
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
            publish_date = publish_date.replace('\n'," ")
            publish_date = re.findall('\d+ \w+. \d{4}',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            try:
                publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
                publish_date = publish_date.replace('\n'," ")
                publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)  
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -None
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Services=Service','Travaux=Works','Fournitures=Supply')

    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'div.cons_categorie').text
        if "Services" in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        elif "Fournitures" in notice_contract_type:
            notice_data.notice_contract_type = "Supply"
        elif "Travaux" in notice_contract_type:
            notice_data.notice_contract_type = "Works"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.objet-line > div > div:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_title = page_details.find_element(By.XPATH, '//*[contains(text(),"Objet :")]//following::div[1]').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet :
    # Onsite Comment -None

    try:
        notice_data.notice_summary_english = notice_data.notice_title
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get lot_details.  	2.click on "div > span > a" to get lot_details from page_details. 		3.reference_url "https://pmp.b2g.etat.lu/entreprise/consultation/528290?orgAcronyme=t5y"
    
    try:
        lot_number=1
        url_1 = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li:nth-child(1) > div.lots a').text        
        url1 = tender_html_element.find_element(By.CSS_SELECTOR, 'ul > li:nth-child(1) > div.lots a').get_attribute("href")
        url2=url1.split('id')[1].split('&')[0] 
        url3='https://pmp.b2g.etat.lu/index.php?page=Entreprise.PopUpDetailLots&orgAccronyme=t5y&id'+str(url2)+'&lang='
        fn.load_page(page_details1,url3,80)
        
        for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#container > div > div > div > div > div'):
            lot_details_data = lot_details()
            lot_details_data.lot_number=lot_number
            single_record.click()
            
            lot_details_data.lot_title = single_record.text.split(":")[1]
            lot_details_data.lot_title_english =GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
            
            try:
                lot_details_data.lot_quantity=url_1.split(' ')[0]
                lot_details_data.lot_quantity_uom=url_1.split(' ')[1]
            except Exception as e:
                logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                pass
            
            try:
                lot_details_data.lot_actual_number = single_record.text.split(":")[0]
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass
            
            try:
                lot_cpvs_data = lot_cpvs()
                lot_cpv = page_details1.find_element(By.XPATH, '//*[contains(text(),"CPV")]//following::span[1]').text
                lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv)[0]
                lot_cpvs_data.lot_cpvs_cleanup()
                lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                pass
        
#         # Onsite Field -Catégorie :
#         # Onsite Comment -click on '+' to get the data and Replace following keywords with given respective keywords ('Travaux = works','Fournitures = supply','Services = Services')

            try:
                lot_details_data.contract_type = notice_data.notice_contract_type
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number += 1
    except Exception as e:
        pass


    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.m-b-10').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#collapseHeading > div.panel-heading.clearfix")))
        page_details.execute_script("arguments[0].click();",click)
        time.sleep(5)
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.panel-heading.clearfix > h1')))
    except:
        pass
    
    
    # Onsite Field -Date et heure limite de remise des plis :
    # Onsite Comment -None

    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Date et heure limite de remise des plis :")]//following::span[1]').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    

    # Onsite Field -Procédure :
    # Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get type_of_procedure_actual.	 	2.split type_of_procedure_actual eg., here "10 européenne ouverte" take only "européenne ouverte".
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Procédure :")]//following::div[1]').text
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        type_of_procedure = type_of_procedure_actual.split(" ")[-1].strip()
        notice_data.type_of_procedure = fn.procedure_mapping("assets/lu_etat_procedure.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type d'avis :
    # Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get document_type_description.

    try:
        document_type_description = page_details.find_element(By.CSS_SELECTOR, " li:nth-child(1) > ul > li:nth-child(5) > div").text
        notice_data.document_type_description = GoogleTranslator(source='auto', target='en').translate(document_type_description)
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
# Onsite Field -None
# Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get cpvs.

    try:              
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Code CPV :")]//following::div[1]/span'):
            cpvs_data = cpvs()
        # Onsite Field -None
        # Onsite Comment -1.click on "div.panel-heading > h1" in page_details to get cpvs_code.     2.here "37535200 (Code principal)" take only "37535200" in cpv_code.
            cpv_code = single_record.text
            cpv_code1 = re.findall('\d{8}',cpv_code)[0].strip()
            cpvs_data = cpvs()
            cpvs_data.cpv_code=cpv_code1
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'LU'
        customer_details_data.org_language = 'FR'
        # Onsite Field -Organisme :
        # Onsite Comment -1.split org_name. eg., here "Portail des marchés publics ( - )" take only "Portail des marchés publics" in org_name.

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Service :")]//following::div[1]').text.split("( ")[0].strip()
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'li.picto-link a'):
            attachments_data = attachments()
        # Onsite Field -None
        # Onsite Comment -1.don't grab file_size in file_name. eg.,in "Règlement de consultation - 74,96 Ko" take only "Règlement de consultation"

            attachments_data.file_name = single_record.text
        
        # Onsite Field -None
        # Onsite Comment -1.don't grab file_name in file_size. eg.,"Règlement de consultation - 74,96 Ko" take only "74,96 Ko".

            try:
                file_size = single_record.text
                file_size =GoogleTranslator(source='auto', target='en').translate(file_size)
                attachments_data.file_size = file_size.split("-")[1].strip()
            except Exception as e:
                logging.info("Exception in file_size: {}".format(type(e).__name__))
                pass
        
        # Onsite Field -None
        # Onsite Comment -1.take this also in external_url "#panelPieces > ul >li > span > a" from page_details.

            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass
    
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
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://pmp.b2g.etat.lu/?page=Entreprise.EntrepriseAdvancedSearch&searchAnnCons"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        page_main.find_element(By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_AdvancedSearch_dateMiseEnLigneStart").clear()
        
        page_main.find_element(By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_AdvancedSearch_dateMiseEnLigneEnd").clear() 
        
        try:
            page_main.find_element(By.CSS_SELECTOR,'#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche').click()
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#cons_ref > div > ul > li:nth-child(1)')))
        except:
            pass

        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div/div[2]'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#ctl0_CONTENU_PAGE_resultSearch_PagerBottom_ctl2 > span > i")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/form/main/div[3]/div/div/div[1]/div[4]/div/div[2]/div[2]/div/div[2]'),page_check))
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
    page_details1.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
