from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "ma_mcamorocco_spn"
log_config.log(SCRIPT_NAME)
import re
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from deep_translator import GoogleTranslator
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "ma_mcamorocco_spn"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

#note:after opening the url click on "Appels d'offres" this keyword in tender_html_element.

    notice_data.script_name = 'ma_mcamorocco_spn'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'MA'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'MAD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'FR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -Numéro
    # Onsite Comment -None

    try:
        notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
        if notice_no !='':
            notice_data.notice_no = notice_no
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Objet
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#block-mca-content > article').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        
    # Onsite Field -None
    # Onsite Comment -in the given field "div:nth-child(3) > p:nth-child(2) > span > span > span > b" written as "AVIS D’ATTRIBUTION DE CONTRATS=NOTICE OF CONTRACT AWARD" then take notice_type=7, otherwise take notice_type=4.
    try:
        publish_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Date publication")]//following::div[1]').text
        publish_date = re.findall('\d+/\d+/\d{4} - \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d/%m/%Y - %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

        # Onsite Field -Date limite
        # Onsite Comment -None
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Date limite")]//following::div[1]').text
        notice_deadline = GoogleTranslator(source='fr', target='en').translate(notice_deadline)
        notice_deadline = re.findall('\w+ \d+, \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d, %Y').strftime('%Y/%m/%d %H:%M:%S')       
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        notice_type = page_details.find_element(By.CSS_SELECTOR, 'div:nth-child(3) > p:nth-child(2) > span > span > span > b').text
        if 'AVIS D’ATTRIBUTION DE CONTRATS' in notice_type:
            notice_data.notice_type = 7
        else:
            notice_data.notice_type = 4
            
    except Exception as e: 
        logging.info("Exception in notice_type: {}".format(type(e).__name__))
        pass
    # Onsite Field -Documents à télécharger
# Onsite Comment -None
# reference_url=https://www.mcamorocco.ma/fr/li-59-deploiement-de-systemes-informatiques-gmao-gestion-de-la-maintenance-assistee-par-ordinateur

    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div > div.row.li-style > div > a'):
            attachments_data = attachments()
        # Onsite Field -Documents à télécharger
        # Onsite Comment -None

            attachments_data.file_name = single_record.text

            attachments_data.external_url = single_record.get_attribute('href')
            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass           
#Format 1:
# ref_url:"https://www.mcamorocco.ma/fr/li-59-deploiement-de-systemes-informatiques-gmao-gestion-de-la-maintenance-assistee-par-ordinateur"   
    
    # Onsite Field -Date publication
    # Onsite Comment -None
    if notice_data.notice_type == 4:
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = 'MILLENNIUM CHALLENGE ACCOUNT (MCA)-Morocco'
            customer_details_data.org_parent_id = '7586426'
            customer_details_data.org_country = 'MA'
            customer_details_data.org_language = 'FR' 

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
    
# Formate 2
# reference_url=https://www.mcamorocco.ma/fr/liste-des-contrats-signes-du-mois-de-fevrier-2023
# in the given field "div:nth-child(3) > p:nth-child(2) > span > span > span > b" written as "AVIS D’ATTRIBUTION DE CONTRATS = NOTICE OF CONTRACT AWARD" then take notice_type=7, otherwise take notice_type=4.

    if notice_data.notice_type == 7:
        try:              
            customer_details_data = customer_details()
            customer_details_data.org_name = 'MILLENNIUM CHALLENGE ACCOUNT (MCA)-Morocco'
            customer_details_data.org_parent_id = '7586426'
            customer_details_data.org_country = 'MA'
            customer_details_data.org_language = 'FR'

        # Onsite Field -Ville
        # Onsite Comment -None

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Ville")]//following::b[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass  

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:              
            funding_agencies_data = funding_agencies()

            funding_agencies_data.funding_agency = 1344862

            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        except Exception as e:
            logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
            pass


        try:
            lot_number = 1
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > table > tbody > tr'):
                lot_details_data = lot_details()
            # Onsite Field -Marché N°
            # Onsite Comment -None
                lot_details_data.lot_number = lot_number
                try:
                    lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'table > tbody > tr > td:nth-child(5)').text
                    lot_details_data.lot_title_english = GoogleTranslator(source='fr', target='en').translate(lot_details_data.lot_title)
                except:
                        lot_details_data.lot_title = notice_data.local_title
                        lot_details_data.lot_title_english = notice_data.notice_title
                        notice_data.is_lot_default = True
                try:
                    award_details_data = award_details()
    
                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

                    # Onsite Field -Montant du contrat (Hors TVA et Hors Droits de Douane)
                    # Onsite Comment -None
                    try:
                        netawardvaluelc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                        netawardvaluelc = re.sub("[^\d\.\,]","",netawardvaluelc)
                        award_details_data.netawardvaluelc =float(netawardvaluelc.replace(',','.').strip())
                    except:
                        pass

                    # Onsite Field -Période du contrat >> Date de signature
                    # Onsite Comment -None
                    try:
                        award_date = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > p:nth-child(2) > span').text
                        award_date = GoogleTranslator(source='auto', target='en').translate(award_date)
                        award_date = re.findall('\w+ \d+, \d{4}',award_date)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%B %d, %Y').strftime('%Y/%m/%d')
                    except:
                        pass
			
                # Onsite Field -Période du contrat >> Délai de livraison
                # Onsite Comment -None
                    try:
                        award_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4) > p:nth-child(4) > span').text
                    except:
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass
                lot_number += 1
                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = webdriver.Chrome(options=options) 
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)    
    urls = ["https://www.mcamorocco.ma/fr/appels-d-offres"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

	try:
	    for page_no in range(1,10):
	        page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="tab_content_offres"]/div/table/tbody/tr'))).text
	        rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tab_content_offres"]/div/table/tbody/tr')))
		length = len(rows)
		for records in range(0,length):
		    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="tab_content_offres"]/div/table/tbody/tr')))[records]
		    extract_and_save_notice(tender_html_element)
		    if notice_count >= MAX_NOTICES:
		        break
	
		    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
		        break
	
		if notice_data.publish_date is not None and notice_data.publish_date < threshold:
		    break

		try:   
		    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/div[1]/div[3]/div/div/div[2]/div[2]/div[1]/div/ul/li[11]/a')))
		    page_main.execute_script("arguments[0].click();",next_page)
		    logging.info("Next page")
		    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="tab_content_offres"]/div/table/tbody/tr'),page_check))
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
    
