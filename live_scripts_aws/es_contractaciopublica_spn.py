from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "es_contractaciopublica_spn"
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
import gec_common.Doc_Download_ingate

#after opening the url select only "Preliminary market consultation" and "Tender announcements within deadline date" and "Execution" this three in "Valid phase" section and then click on "Apply Filters" for tender_details.

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "es_contractaciopublica_spn"
Doc_Download = gec_common.Doc_Download_ingate.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'ES'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'EUR'
    
    notice_data.main_language = 'ES'

    notice_data.procurement_method = 0

    notice_data.notice_type = 4
    
    notice_data.script_name = "es_contractaciopublica_spn"

    # Onsite Comment -Note:take only text

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada > div > div > a').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada > div > div > div.d-flex.flex-column.gap-1 > div:nth-child(1)').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada > div > div > div.d-flex.gap-1.fases-vigents > div.d-flex.flex-column.text-center > a').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "app-resultats-cerca-avancada > div > div > div.d-flex.gap-1.fases-vigents > div.d-flex.flex-column.text-center > span").text
        publish_date = re.findall('\d+/\d+/\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%m/%d/%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    # Onsite Field -Basic budget for tender (excluding VAT)

    try:
        grossbudgetlc = tender_html_element.find_element(By.CSS_SELECTOR, 'app-resultats-cerca-avancada > div > div > div.d-flex.flex-column.gap-1 > div:nth-child(2) > span:nth-child(2)').text
        grossbudgetlc = re.sub("[^\d\.\,]", "",grossbudgetlc)
        notice_data.netbudgeteuro = float(grossbudgetlc.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Basic budget for tender (excluding VAT)

    try:
        notice_data.additional_tender_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div > div.d-flex.flex-column.gap-1 > div:nth-child(3) > a').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.gap-1.fases-vigents > div.d-flex.flex-column.text-center > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    try:
        cookies_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/ngb-modal-window/div/div/ngc-cookie-consent-modal/div/div/div/button[2]')))
        page_details.execute_script("arguments[0].click();",cookies_click)
    except:
        pass
    time.sleep(5)
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.class_at_source = 'CPV'
    
    # Onsite Field -Expedient code
    # Onsite Comment -None

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Expedient code:")]//following::span[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        further_info1 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'app-dades-organ-publicacio > div > app-mes-informacio > div > button')))
        page_details.execute_script("arguments[0].click();",further_info1)

        further_info2 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'app-anunci-licitacio-objecte > div > app-mes-informacio > div > button')))
        page_details.execute_script("arguments[0].click();",further_info2)

        further_info3 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'app-anunci-licitacio-procediment > div > app-mes-informacio > div > button')))
        page_details.execute_script("arguments[0].click();",further_info3)

        further_info4 = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'app-anunci-licitacio-informacio-complementaria > div > app-mes-informacio > div > button')))
        page_details.execute_script("arguments[0].click();",further_info4)
        time.sleep(5)
    except:
        pass
    
    # Onsite Field -Type of contract
    # Onsite Comment -Note:Repleace following keywords with given keywords("Work projects=Works","Supplies=Supply","Services=Service")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::div[1]').text
        notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::div[1]').text
        if 'Work projects' in notice_contract_type:
            notice_data.notice_contract_type = 'Works'
        elif 'Supplies' in notice_contract_type:
            notice_data.notice_contract_type = 'Supply'
        elif 'Services' in notice_contract_type:
             notice_data.notice_contract_type = 'Service'
        else:
            pass   
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Type of contract
    # Onsite Comment -None
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'app-detall-publicacio').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    
    # Onsite Field -Procedure >> Contract award procedure
    # Onsite Comment -None

    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract award procedure")]//following::div[1]').text
        type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
        notice_data.type_of_procedure = fn.procedure_mapping("assets/es_contractaciopublica_spn.csv",type_of_procedure)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject>> Estimated value of contract
    # Onsite Comment -None

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Estimated value of contract")]//following::div[1]').text
        est_amount = re.sub("[^\d\.\,]", "",est_amount)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject >> Basic estimate for tender
    # Onsite Comment -None

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Basic estimate for tender")]//following::div[1]').text
        netbudgetlc = re.sub("[^\d\.\,]", "",netbudgetlc)
        notice_data.netbudgetlc = float(netbudgetlc.replace(',','').strip())
        notice_data.netbudgeteuro = notice_data.netbudgetlc
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject >> Basic estimate for tender
    # Onsite Comment -None

    
    # Onsite Field -Subject >> VAT
    # Onsite Comment -None

    try:
        vat = page_details.find_element(By.XPATH, '//span[starts-with(text(),"VAT:")]/../following-sibling::div').text.split('%')[0].strip()
        notice_data.vat = float(vat)
    except Exception as e:
        logging.info("Exception in vat: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Subject  >> Duration of the contract
    # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duration of the contract")]//following::div[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
        
# Onsite Field -None
# Onsite Comment -None

    try:              
        cpvs_code =  page_details.find_elements(By.CSS_SELECTOR, 'app-anunci-licitacio-objecte-lot > div > div:nth-child(1) > div.col-md-8').text
        # Onsite Field -Subject >> CPV
        # Onsite Comment -None
        cpv_regex = re.compile(r'\d{8}')
        cpvs_data = cpv_regex.findall(cpvs_code)
        for cpv in cpvs_data:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
     # Onsite Field -Subject >> CPV
    # Onsite Comment -None
    try:
        cpvs_code =  page_details.find_elements(By.CSS_SELECTOR, 'app-anunci-licitacio-objecte-lot > div > div:nth-child(1) > div.col-md-8').text
        cpv_at_sources = re.findall("\d{8}",cpvs_code)
        cpv_at_source = ''
        for cpv1 in cpv_at_sources:
            cpv_at_source += cpv1  
            cpv_at_source += ',' 
        cpv_source = cpv_at_source.rstrip(',')
        notice_data.cpv_at_source = cpv_source
    except:
        pass
# Onsite Field -Contract award criteria: > Criterion:
#Note:Click on "Further information" and grab the data
# Onsite Comment -Note:if the "Criterion: is " Price" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  of the if the "Criterion: is " technical" grabb in criteria title  and Weight from  "Weighting out of 100%:" field  if above both keyword avaiable" Price", "technical" than only pass this in criteria title .. do not pass the hole line
#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157846
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-criteris-adjudicacio > div.card.bg-light > div > div'):
            tender_criteria_data = tender_criteria()
        # Onsite Field -Subject >> Criterion

            tender_criteria_title = single_record.find_element(By.XPATH, '//*[contains(text(),"Criterion")]//following::div[1]').text
            if 'price' in tender_criteria_title.lower():
                tender_criteria_data.tender_criteria_title = 'price'
                tender_criteria_data.tender_is_price_related = True
            elif 'technical' in tender_criteria_title.lower():
                tender_criteria_data.tender_criteria_title = 'technical'
        
        # Onsite Field -Subject >> Weighting out of 100%

            tender_criteria_weight = single_record.find_element(By.XPATH, '//*[contains(text(),"Weighting out of 100%")]//following::div[1]').text.split('.00 %')[0].strip()
            tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)
        
            tender_criteria_data.tender_criteria_cleanup()
            notice_data.tender_criteria.append(tender_criteria_data)
    except Exception as e:
        logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
        pass
    
    # Onsite Field -Deadline for the presentation of offers

    try:
        notice_deadline = page_details.find_element(By.XPATH, '''//*[contains(text(),"Deadline for the presentation of offers")]//following::div[1]''').text
        notice_deadline = re.findall('\d+/\d+/\d{4} \d+:\d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%m/%d/%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:  
        customer_details_data = customer_details()

        #reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157276
        # Onsite Comment -Note:Click on "Further information" and grab the data
        
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.d-flex.flex-column.gap-1 > div:nth-child(3)').text
        

        customer_details_data.org_country = 'ES'
        customer_details_data.org_language = 'ES'
    # Onsite Field -Procurement entity >> Postal address

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postal address")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Locality

        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Locality")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Post code

        try:
            customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Post code")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in postal_code: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> NUTS (Nomenclature of Territorial Units for Statistics)

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS (Nomenclature of Territorial Units for Statistics)")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Telephone

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Email address

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"Email address")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Web address

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Web address")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Contact persons >> Name
    # Onsite Comment -Note:"//*[contains(text(),"Contact persons")]//following::div[17]"Take this also data in contact_person. seperate each contact_person using comma(,).
        try:
            contact_person = ''
            for single_record in page_details.find_elements(By.CSS_SELECTOR,'div.camps.collapse.show > div.card.bg-light > div.card-body > div'):
                contact_person += single_record.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > div.col-md-8').text
                contact_person += ','
            customer_details_data.contact_person = contact_person.rstrip(',')
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    # Onsite Field -Procurement entity >> Main activity

        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Main activity")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
            pass

        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157276

    try:
        rows = WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr')))
        length = int(len(rows)/2)
        each_lot = 1
        lot_number = 1
        for records in range(0,length):
            WebDriverWait(page_details, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr')))[records]
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
        # Onsite Field -Subject >> Title of the batch
        # Onsite Comment -Note:splite lot_actual_number
            lot_details_data.lot_class_codes_at_source = 'CPV'
            try:
                lot_details_data.lot_actual_number = page_details.find_element(By.CSS_SELECTOR, '#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr:nth-child('+str(each_lot)+') > td.cdk-cell.cdk-column-titol').text.split('LOT')[1].split(':')[0].strip()
            except Exception as e:
                logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                pass

        # Onsite Field -Subject >> Title of the batch
        # Onsite Comment -None

            lot_details_data.lot_title = page_details.find_element(By.CSS_SELECTOR, '#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr:nth-child('+str(each_lot)+') > td.cdk-cell.cdk-column-titol').text.split(':')[1].strip()
            lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
            
        # Onsite Field -Subject >> Description of the batch
        # Onsite Comment -None

            try:
                lot_details_data.lot_description = page_details.find_element(By.CSS_SELECTOR, '#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr:nth-child('+str(each_lot)+') > td.cdk-cell.cdk-column-descripcio').text
            except Exception as e:
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass

        # Onsite Field -Subject >> Title of the batch >> Basic estimate for tender including VAT
        # Onsite Comment -None
            try:
                drop_d_click = WebDriverWait(page_details, 80).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr:nth-child('+str(each_lot)+') > td.cdk-cell.text-center.cdk-column-expandir > button')))
                page_details.execute_script("arguments[0].click();",drop_d_click)
                time.sleep(7)
                each_lot += 1


                t=page_details.find_element(By.CSS_SELECTOR, '#objecte-panel > div > app-anunci-licitacio-objecte > div > app-taula-lots > ngc-table > div > table > tbody > tr:nth-child('+str(each_lot)+') > td')

                try:
                    lot_netbudget_lc = t.find_element(By.CSS_SELECTOR, 'app-anunci-licitacio-objecte-lot > div > div.camps > div:nth-child(2) > div.col-md-8').text
                    lot_netbudget_lc = re.sub("[^\d\.\,]", "",lot_netbudget_lc)
                    lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(',','').strip())
                    lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                    pass


                try:
                    lot_grossbudget_lc = t.find_element(By.CSS_SELECTOR, 'app-anunci-licitacio-objecte-lot > div > div.camps > div:nth-child(4) > div.col-md-8').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                    lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc.replace(',','').strip())
                    lot_details_data.lot_grossbudget = lot_details_data.lot_grossbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_grossbudgetlc: {}".format(type(e).__name__))
                    pass

                try:
                    for single_record2 in t.find_elements(By.CSS_SELECTOR, 'app-anunci-licitacio-objecte-lot > div > app-criteris-adjudicacio > div.card.bg-light > div > div'):
                        lot_criteria_data = lot_criteria()

                        # Onsite Field -Subject >> Title of the batch >> Criterion
                        # Onsite Comment -None

                        lot_criteria_title = single_record2.find_element(By.CSS_SELECTOR, 'div > div:nth-child(1) > div.col-md-8 > span').text
                        if 'technique' in lot_criteria_title.lower():
                            lot_criteria_data.lot_criteria_title = 'technique'
                        elif 'price' in lot_criteria_title.lower():
                            lot_criteria_data.lot_criteria_title = 'price'

                        if lot_criteria_data.lot_criteria_title == 'price':
                            lot_criteria_data.lot_is_price_related = True


                        lot_criteria_data.lot_criteria_weight = single_record2.find_element(By.CSS_SELECTOR, 'div > div:nth-child(3) > div.col-md-8').text.split('%')[0].strip()

                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__)) 
                    pass

                try:
                    single_record = page_details.find_element(By.CSS_SELECTOR,'//*[contains(text(),"CPV:")]//following::div/span[1]').text
                    cpv_regex = re.compile(r'\d{8}')
                    lot_cpvs_data = cpv_regex.findall(single_record)
                    for cpv in lot_cpvs_data:
                        lot_cpvs_data = lot_cpvs()
                        lot_cpvs_data.lot_cpv_code = cpv
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in cpv_code: {}".format(type(e).__name__)) 
                    pass

                try:
                    single_record = page_details.find_element(By.CSS_SELECTOR,'//*[contains(text(),"CPV:")]//following::div/span[1]').text
                    cpv_regex = re.compile(r'\d{8}')
                    cpv_at_sources = cpv_regex.findall(single_record)
                    cpv_at_source = ''
                    for cpv1 in cpv_at_sources:
                        cpv_at_source += cpv1  
                        cpv_at_source += ',' 
                    cpv_source = cpv_at_source.rstrip(',')
                    lot_details_data.lot_cpv_at_source = cpv_source
                    notice_data.cpv_at_source += ',' + lot_details_data.lot_cpv_at_source
                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass    

                each_lot += 1
            except:
                pass
            lot_number +=1 
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass   

#reference_url=https://contractaciopublica.cat/en/detall-publicacio/200157208
    try:  
        attachments_scroll = page_details.find_element(By.CSS_SELECTOR,'#documentacio-panel-header')
        page_details.execute_script("arguments[0].scrollIntoView(true);", attachments_scroll)
    except:
        pass
        
    try:                                                                  
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'app-documents-publicacio > div > div.col-md-8 > div'):
            attachments_data = attachments()
        # Onsite Field -Documantation
        # Onsite Comment -Note:split file_name.eg.,"Plec de Condicions Particulars.pdf" don't take ".pdf" in file_name.

            attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'div > button').text

    # Onsite Field -Documentation
    # Onsite Comment -Note:split the extention (like ".pdf",".zip") from "file name" field
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'div > button').text.split('.')[-1].strip()
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            external_url = WebDriverWait(single_record, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div > button')))
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(2)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0])

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
page_details = Doc_Download.page_details
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://contractaciopublica.gencat.cat/ecofin_pscp/AppJava/en_GB/search.pscp?pagingPage=0&reqCode=searchCn&aggregatedPublication=false&sortDirection=1&pagingNumberPer=10&lawType=2"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            cookies_click = WebDriverWait(page_main, 90).until(EC.element_to_be_clickable((By.XPATH,'/html/body/ngb-modal-window/div/div/ngc-cookie-consent-modal/div/div/div/button[2]')))
            page_main.execute_script("arguments[0].click();",cookies_click)
        except:
            pass
        
        search_result = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/app-root/main/app-inici/div/div/div[1]/button')))
        page_main.execute_script("arguments[0].click();",search_result)
                                                           
        preliminary_result = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#checkbox-option-2')))
        page_main.execute_script("arguments[0].click();",preliminary_result)
                                                           
        tender_announcement = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#checkbox-option-4')))
        page_main.execute_script("arguments[0].click();",tender_announcement)
                                            
        apply_filter = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'button.btn.btn-primary.flex-grow-1')))
        page_main.execute_script("arguments[0].click();",apply_filter)
        time.sleep(2)
        try:
            for page_no in range(2,6):
                page_check = WebDriverWait(page_main, 180).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#resultats-cerca-avancada > app-resultats-cerca-avancada > div'))).text
                rows = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#resultats-cerca-avancada > app-resultats-cerca-avancada > div')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 180).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#resultats-cerca-avancada > app-resultats-cerca-avancada > div')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#resultats-cerca-avancada > app-resultats-cerca-avancada > div'),page_check))
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
