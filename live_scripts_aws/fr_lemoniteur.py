from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fr_lemoniteur"
log_config.log(SCRIPT_NAME)
import re
import jsons
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
SCRIPT_NAME = "fr_lemoniteur"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'fr_lemoniteur'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FR'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.main_language = 'FR'
    
    notice_data.currency = 'EUR'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 4 
 
    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'a > p.cartoucheGene__number').text.split(": ")[1]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_contract_type = tender_html_element.find_element(By.CSS_SELECTOR, 'a:nth-child(n) > div.cartoucheGene__subGroup.cartoucheGene__subGroup--left > p:nth-child(2)').text
        notice_contract_type = GoogleTranslator(source='auto', target='en').translate(notice_contract_type)
        if'works' in notice_contract_type or "Public Works" in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif'Stationery' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif'Services' in notice_contract_type:
            notice_data.notice_contract_type = "Service"
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.type_of_procedure_actual = tender_html_element.find_element(By.CSS_SELECTOR, "div.cartoucheGene__subGroup > p:nth-child(3)").text
        type_of_procedure_actual_en = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/fr_lemoniteur_procedure.csv",type_of_procedure_actual_en)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    
    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "p.cartoucheGene__deadline > span").text
        notice_deadline = re.findall('\d+/\d+/\d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
        return

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " div:nth-child(5) > p.cartoucheGene__regular").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass    
    
    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_url = tender_html_element.get_attribute("href")   
        fn.load_page(page_details,notice_data.notice_url,80)
        
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#cmpargustestagree1'))).click()
    except:
        pass
    
    try:
        WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' section.cartoucheGene__block.cartoucheGene__block--pageDetail > p:nth-child(4)')))
    except:
        pass
        
    try:
        org_name = page_details.find_element(By.CSS_SELECTOR, "p.cartoucheGene__subtitle").text.split(": ")[1]
    except:
        pass
    

    try:
        notice_data.local_title = page_details.find_element(By.CSS_SELECTOR, ' h2.cartoucheGene__title').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_text = page_details.find_element(By.CSS_SELECTOR, 'div.theme__lme.pageSpeMOL').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'section.pageDetail__content').text.split("Description succincte du marché :")[1].split("Lieu principal d'exécution du marché :")[0].split("Estimated value (excluding tax):")[0].split("espaces à vivre et mise en conformité des équipements techniques :")[0].strip()
    except:
        try:
            local_description = page_details.find_element(By.CSS_SELECTOR, 'section.pageDetail__content').text.split("Description :")[1].split("2.1.2 Division en lots :")[0].split("Estimated value (excluding tax):")[0].split("Classification CPV :")[0].strip()
            if len(local_description)< 1:
                pass
            else:
                notice_data.local_description = local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        dispatch_date = page_details.find_element(By.CSS_SELECTOR, 'section.pageDetail__content').text.split('du présent avis :')[1]
        dispatch_date = GoogleTranslator(source='auto', target='en').translate(dispatch_date)
        try:
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.grossbudgetlc = page_details.find_element(By.CSS_SELECTOR, "section.pageDetail__content").text.split('Valeur totale estimée ')[1].split("euros ")[0].split('TVA')[1]
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    

    try: 
        data = page_details.find_element(By.CSS_SELECTOR,'section.pageDetail__content').text
        if "Principale :" in data:
            cpvss = data.split("Principale : ")[1:]
            for l in cpvss:
                cpvs_data = cpvs()
                cpv_code = l.split("\n")[0]
                cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:  
        lot_data = page_details.find_element(By.CSS_SELECTOR,'section.pageDetail__content').text
        if "Description du lot :" in lot_data:
            
            lot_data1 = lot_data.split("Description du lot : ")[1:]
            lot_number = 1
            for l in lot_data1:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                try:
                    lot_details_data.lot_title = l.split("\n")[0]
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass

                try:
                    lot_actual_number = lot_details_data.lot_title
                    lot_details_data.lot_actual_number= re.findall('Lot \d+',lot_actual_number)[0]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = cpvs_data.cpv_code

                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
        elif "Lot n°" in lot_data:
            lot_data1 = lot_data.split("Lot n°")[1:]
            lot_number = 1
            for l in lot_data1:
                lot_details_data = lot_details()
                lot_details_data.lot_number =  lot_number
                try:
                    lot_title = l.split("\n")[0]
                    lot_details_data.lot_title = lot_title
                    lot_details_data.lot_title = lot_title.split("- ")[1].split("- CPV")[0]
                    lot_details_data.lot_title = lot_details_data.lot_title
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                except Exception as e:
                    logging.info("Exception in lot_title: {}".format(type(e).__name__))
                    pass

                try:
                    lot_actual_number = lot_title
                    lot_details_data.lot_actual_number= re.findall('\d+',lot_actual_number)[0]
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpvs_data.lot_cpv_code = lot_title.split("- CPV")[1].split("\n")[0].strip()
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass
            
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number += 1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass
    

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'FR'
        customer_details_data.org_language = 'FR'
        customer_details_data.org_name = org_name
            
        try:
            customer_details_data.org_address = page_details.find_element(By.CSS_SELECTOR, ' div.colLeft.marginTop25.cartoucheGene.pageDetail > section.cartoucheGene__block.cartoucheGene__block--pageDetail > div.cartoucheGene__subGroup.cartoucheGene__subGroup--left > p:nth-child(1)').text
        except:
            pass
        
        try:
            customer_details_data.customer_nuts = page_details.find_element(By.CSS_SELECTOR, 'section.pageDetail__content').text.split('NUTS :')[1].split("\n")[0]
        except:
            pass
            
        try:
            customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'section.pageDetail__content').text.split('mail du contact : ')[1].split("\n")[0]
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
    
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:              
        tender_cri = page_details.find_element(By.CSS_SELECTOR,'section.pageDetail__content').text
        if "Critères d'attribution :" in tender_cri:
            tender_cri1 = tender_cri.split("Offre économiquement la plus avantageuse appréciée en fonction des critères énoncés ci-dessous avec leur pondération :")[1].split("II.2.6) Valeur estimée :")[0].split("Renseignements d'ordre administratifs :")[0].split("II.")[0].split("Section 4 ")[0].strip()
            for l in tender_cri1.split('\n'):
                tender_criteria_data = tender_criteria()
                tender_criteria_data.tender_criteria_title = l
                tender_criteria_weight = l
                tender_criteria_weight = re.findall('\d+ %',tender_criteria_weight)[0]
                tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
                tender_criteria_data.tender_criteria_cleanup()
                notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass

    try:              
        funding_agencies_data = funding_agencies()
    
        funding_agencies_data.funding_agency = page_details.find_element(By.CSS_SELECTOR, 'section.pageDetail__content').text
        
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.CSS_SELECTOR, 'div.pageDetail__printPdf > p:nth-child(2) > a').get_attribute("href")
        logging.info(notice_data.additional_tender_url)
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        notice_data.additional_tender_url = url
    
    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_details = fn.init_chrome_driver(arguments) 
page_main = fn.init_chrome_driver(arguments) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.lemoniteur.fr/appels-offres/"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#cmpargustestagree1'))).click()
        except:
            pass
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' p.cartoucheGene__headline')))
        except:
            pass
        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,' div.blocListMOL > div > a:nth-child(n)'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div.blocListMOL > div > a:nth-child(n)')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ' div.blocListMOL > div > a:nth-child(n)')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,' div.blocListMOL > div > a:nth-child(n)'),page_check))
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
