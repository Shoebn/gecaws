from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ca_seao_spn"
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

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ca_seao_spn"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
 #-----------click on "Recherche avancée" then click "Rechercher" and then In "Statuts" select "Publié" and "Annulé" to get tender data and rest should be "all"----------------#  
 
    notice_data.script_name = 'ca_seao_spn'
    notice_data.main_language = 'FR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'CA'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 2
    notice_data.notice_type = 4
    notice_data.currency = 'CAD'
    
    notice_data.class_at_source= 'UNSPSC'

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text
        try:
            publish_date = re.findall('\d{4}-\d+-\d+ \d+ h \d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d %H h %M').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
            notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Fermeture
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        try:
            notice_deadline = re.findall('\d{4}-\d+-\d+ \d+ h',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d %H h').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
        except:
            notice_deadline = re.findall('\d{4}-\d+-\d+',notice_deadline)[0]
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
         notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    except:
        pass
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
        
        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Numéro')])[1]//following::span[1]''').text
        except Exception as e:
            logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
            pass
        
         # Onsite Field -Titre
        try:
            notice_data.local_title = page_details.find_element(By.XPATH, '''(//*[contains(text(),'Titre')])[1]//following::span[1]''').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Description    
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Description')]//following::div[1]").text
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Type de l'avis :
        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, "//*[contains(text(),'Type de ')]//following::span [1]").text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

        # Onsite Field -Type de l'avis :  --- Travaux de construction - Works Approvisionnement (biens) - Goods Services de nature technique - Services Services professionnels - Services
        # Onsite Comment -refer number "1751687"
        try:
            notice_data.notice_no = page_details.find_element(By.XPATH, "//*[contains(text(),'référence')]//following::span [1]").text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Type de l'avis :
        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Nature du contrat :')]//following::span [1]").text
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#dvOpportunityDetail').get_attribute("outerHTML")                     
        except:
            pass
        
        try:              
            customer_details_data = customer_details()

            customer_details_data.org_name = page_details.find_element(By.XPATH, "//*[contains(text(),'Organisme')]//following::span [1]").text

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, "//*[contains(text(),'Adresse')]//following::span [1]").text
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            # Onsite Field -split "Telephone" and "number" from the selector--just take number
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, "//*[contains(text(),'Téléphone')]").text.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            # Onsite Field -split contact person from "Contact" to "Telephone"
            try:
                contact_person = page_details.find_element(By.XPATH, "//*[contains(text(),'Contact')]//following::td [1]").text.split("Téléphone")[0].strip()
                if ':' in contact_person:
                    customer_details_data.contact_person = contact_person.split(':')[0].strip()
                else:
                    customer_details_data.contact_person = contact_person
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            # Onsite Field -split contact person from "Contact" to "Telephone"
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, "//*[contains(text(),'Courriel')]").text.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
            
            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, "//*[contains(text(),'Site Web')]//following::td[1]").text.split(':')[1].strip()
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'CA'
            customer_details_data.org_language = 'FR'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
        
        try:              
            notice_text = page_details.find_element(By.CSS_SELECTOR, '#dvOpportunityDetail').text
            if 'LOT' in notice_text:
                lot_data = notice_text.split('LOT')[1:3]
                lot_number = 1
                for single_record in lot_data:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    # Onsite Field -just take following data ----take data which is after "lot"
                    lot_details_data.lot_title = single_record.split('\n')[0].strip()
                    lot_details_data.lot_title_english = lot_details_data.lot_title
                    lot_details_data.lot_description = lot_details_data.lot_title
                    lot_details_data.lot_description_english = lot_details_data.lot_title

                    # Onsite Field -just take following data ----take data which is after "lot"
                    # Onsite Comment -"https://seao.ca/OpportunityPublication/ConsulterAvis/Recherche?callingPage=3&ItemId=f7cb8b65-551f-481f-9a77-ab31cb7cf806&COpp=Search&p=3&searchId=6bad23dd-db01-4601-a4e0-b0c100412438"
                    try:
                        lot_details_data.lot_actual_number = single_record.split(' ')[0].strip()
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass

                    # Onsite Field -just take following data ----take data which is after "lot"
                    try:
                        lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, "//*[contains(text(),'Nature du contrat :')]//following::span [1]").text
                    except Exception as e:
                        logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                        pass

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

        try:  
            cpv_at_source = ''
            cpv_title = ''
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#pnlUNSPSC > div:nth-child(1) > div.data > ul > li'):
                cpv_code = single_record.text
                cpv_codes = re.findall('\d{8}',cpv_code)[0]
                cpv_title += cpv_code.replace(cpv_codes ,'').strip()
                cpv_title += ','
                cpv_codes_list = fn.CPV_mapping("assets/ca_seao_spn_cpv.csv",cpv_codes)
                for each_cpv in cpv_codes_list:
                    cpvs_data = cpvs()
                    cpvs_data.cpv_code = each_cpv
                    cpv_at_source += each_cpv
                    cpv_at_source += ','
                    cpvs_data.cpvs_cleanup()
                    notice_data.cpvs.append(cpvs_data)
            notice_data.cpv_at_source = cpv_at_source.rstrip(',')
            notice_data.class_codes_at_source = notice_data.cpv_at_source
            notice_data.class_title_at_source = cpv_title.rstrip(',')
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__))
            pass  
        
        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#pnlDocDistrib > table > tbody > tr')[1:]:
                external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute('href')
                if external_url is not None:
                    attachments_data = attachments()

                    attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(6) > a').get_attribute('href')

                    attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text

                    try:
                        attachments_data.file_description = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
                    except Exception as e:
                        logging.info("Exception in file_description: {}".format(type(e).__name__))
                        pass

                    try:
                        attachments_data.file_size = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                    except Exception as e:
                        logging.info("Exception in file_size: {}".format(type(e).__name__))
                        pass

                    attachments_data.attachments_cleanup()
                    notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass
        
        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#trSummaryCriterias > span > p'):
                tender_criteria_data = tender_criteria()
                # Onsite Field -Critères de sélection
                # Onsite Comment -split title from selector
                tender_criteria_data.tender_criteria_title = single_record.find_element(By.CSS_SELECTOR, 'p').text.split('(')[0].strip()

                # Onsite Comment -split weight from selector 
                tender_criteria_weight = single_record.find_element(By.CSS_SELECTOR, 'p').text.split('poids :')[1].split('%')[0].strip()
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass
        
         # Onsite Field -Durée prévue du contrat sans les options (en mois)
        try:
            contract_duration_word = page_details.find_element(By.XPATH, '''//*[contains(text(),"Durée prévue du contrat sans les options (en mois) :")]''').text.split('(')[1].split(')')[0].strip()
            contract_duration_num = page_details.find_element(By.XPATH, '''//*[contains(text(),"Durée prévue du contrat sans les options (en mois) :")]//following::td[1]''').text
            notice_data.contract_duration = contract_duration_word + ':' + contract_duration_num
        except Exception as e:
            logging.info("Exception in contract_duration: {}".format(type(e).__name__))
            pass

       # Onsite Field -Catégorie
        try:
            notice_data.category = page_details.find_element(By.CSS_SELECTOR, '#pnlUNSPSC > div:nth-child(3) > div.data > ul > li').text
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass
    
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    logging.info(notice_data.identifier)
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
    urls = ['https://seao.ca/Recherche/avis_trouves.aspx?callingPage=3&Results=1&searchId=d854e9d4-6cf6-4f34-9689-b0c10014468d#p=1'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        recherche_avancée = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#hlAdvanced'))).click()
        time.sleep(3)
        
        rechercher = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#ctl00_ctl00_phContent_phLeftBigCol_ctl00_searchAdv1Button'))).click()
        time.sleep(3)
        
        Publié = WebDriverWait(page_main, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#OpportunityStatusFilter_6'))).click()
        time.sleep(5)

        try:
            Annulé = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#OpportunityStatusFilter_7'))).click()
            time.sleep(5)
        except:
            pass

        try:
            for page_no in range(1,6):
                page_check = WebDriverWait(page_main, 80).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tblResults"]/tbody/tr[2]'))).text
                rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblResults"]/tbody/tr')))
                length = len(rows)
                for records in range(1,length):
                    tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tblResults"]/tbody/tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="PageNext"]')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tblResults"]/tbody/tr[2]'),page_check))
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
    output_json_file.copyFinalJSONToServer(output_json_folder)  

