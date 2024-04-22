from gec_common.gecclass import *
import logging
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
import gec_common.Doc_Download_ingate as Doc_Download
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "nl_tenderned_spn"
Doc_Download = Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"

def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    
    notice_data.main_language = 'NL'
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NL'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    notice_data.procurement_method = 2
    try:
        notice_type = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div').text
        if 'Aankondiging van wijziging van een opdracht' in notice_type or 'Rectificatie' in notice_type:
            notice_data.notice_type = 16
            notice_data.script_name = 'nl_tenderned_amd'
        else:
            notice_data.notice_type = 4
            notice_data.script_name = 'nl_tenderned_spn'
    except:
        pass
    
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-title>h3').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except:
        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'span.tn-h3 > a').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "div:nth-child(2) > font").text
        publish_date = publish_date.split('-')[0].strip()
        publish_date = GoogleTranslator(source='nl', target='en').translate(publish_date)
        notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except:
        try:
            publish_date = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text
            publish_date = publish_date.split('-')[0].strip()
            publish_date = GoogleTranslator(source='auto', target='en').translate(publish_date)
            notice_data.publish_date = datetime.strptime(publish_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except Exception as e:
            logging.info("Exception in publish_date: {}".format(type(e).__name__))
            pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "mat-card-content > div:nth-child(1) > div:nth-child(2)").text  
        notice_deadline = GoogleTranslator(source='nl', target='en').translate(notice_deadline)

        try:
            notice_deadline = re.findall('\w+ \d+ \d{4}, \d+:\d+ [apAP][mM]',notice_deadline)[0]
        except:
            pass
        
        try:
            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d %Y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        except:
            try:
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d %Y, %H:%M').strftime('%Y/%m/%d %H:%M:%S')  
            except:
                try:
                    notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d %Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    try:
                        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d %Y, %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        try:
                            notice_data.notice_deadline = datetime.strptime(notice_deadline,'%B %d %Y').strftime('%Y/%m/%d %H:%M:%S')
                        except:
                            try:
                                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%b %d, %Y, %I:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                            except:
                                pass
                            
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass

    try:
        type_of_procedure_actual  = tender_html_element.find_element(By.XPATH, '//*[contains(text(),"Procedure")]//following::span[1]').text  
        type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(type_of_procedure_actual)  
        notice_data.type_of_procedure = fn.procedure_mapping("assets/nl_tenderned.csv",type_of_procedure_actual)        
        notice_data.type_of_procedure_actual = type_of_procedure_actual
        
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = tender_html_element.text.split("Type opdracht")[1].split("\n")[1]
        if 'Leveringen' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Diensten' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Werken' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass  

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'a.tn-link').get_attribute("href")   
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = notice_data.notice_url.split('/')[-1]
    except:
        try:
            notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Referentienummer")]//following::div[1]').text
            if '-' not in notice_no:
                notice_data.notice_no = notice_no
            else:
                notice_data.notice_no = notice_data.notice_url.split('/')[-1]

        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    try:
        tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvang opdracht")]//following::div[1]').text 
        
        if '-' not in tender_contract_start_date:
            tender_contract_start_date = GoogleTranslator(source='nl', target='en').translate(tender_contract_start_date)
            try:
                notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')  
            except:
                try:
                    notice_data.tender_contract_start_date   = datetime.strptime(tender_contract_start_date ,'%B %d %Y').strftime('%Y/%m/%d %H:%M:%S')  
                except:
                    try:
                        notice_data.tender_contract_start_date   = datetime.strptime(tender_contract_start_date ,'%b %d %Y').strftime('%Y/%m/%d %H:%M:%S')  
                    except:
                        pass
    except Exception as e:
        logging.info("Exception in tender_contract_start_date: {}".format(type(e).__name__))
        pass

    try:
        tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Voltooiing opdracht")]//following::div[1]').text  
        tender_contract_end_date = GoogleTranslator(source='nl', target='en').translate(tender_contract_end_date)
        try:
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %b. %Y').strftime('%Y/%m/%d %H:%M:%S')         
        except:
            try:
                notice_data.tender_contract_end_date   = datetime.strptime(tender_contract_end_date ,'%B %d %Y').strftime('%Y/%m/%d %H:%M:%S')  
            except:
                try:
                    notice_data.tender_contract_end_date   = datetime.strptime(tender_contract_end_date ,'%b %d %Y').strftime('%Y/%m/%d %H:%M:%S')  
                except:
                    try:
                        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%b %d, %Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass

    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass 

    try:
        cpv_at_source = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdopdracht (CPV code)")]//following::div[1]').text 
        notice_data.cpv_at_source = re.findall("\d{8}",cpv_at_source)[0]
        notice_data.class_at_source = 'CPV' 
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

    try:
        for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Bijkomende opdracht(-en) (CPV code)")]//following::div[1]/div'):  
            cpvs_data = cpvs()

            text1 = single_record.text
        
            text1 = text1.split('-')[0]
            cpv_at_sources = re.findall("\d{8}",text1)
            cpv_at_source = ''
            for cpv1 in cpv_at_sources:
                cpv_at_source += cpv1  
                cpv_at_source += ',' 
            cpv_source = cpv_at_source.rstrip(',')
            notice_data.cpv_at_source = notice_data.cpv_at_source + ',' + cpv_source
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass    

    try:              
        try:
            cpvs_data = cpvs()
            
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdopdracht (CPV code)")]//following::div[1]').text 
            cpvs_data.cpv_code = re.findall("\d{8}",cpv_code)[0]            
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

        try:
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Bijkomende opdracht(-en) (CPV code)")]//following::div[1]/div'):  
                cpvs_data = cpvs()

                cpv_code = single_record.text
                cpvs_data.cpv_code = re.findall("\d{8}",cpv_code)[0]

                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass

    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
           
    try:
        Publicatie_click = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Publicatie")]')))  
        page_details.execute_script("arguments[0].click();",Publicatie_click)
        time.sleep(5)
    except:
        pass            
    
    try:
        Procedure_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Procedure")]')))  
        page_details.execute_script("arguments[0].click();",Procedure_clk)
        time.sleep(5)
    except:
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Korte beschrijving")]//following::p[2]').text
    except:
        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Beschrijving")]//following::span[2]').text
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    
    try:
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)  
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'mat-card-header > div > mat-card-subtitle > div:nth-child(2)').text 
        notice_data.document_type_description = document_type_description.split('-')[1].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        funding_agencies = page_details.find_element(By.XPATH,'//*[contains(text(),"Inlichtingen over middelen van de Europese Unie")]//following::p[1]').text  
        if 'neen' not in funding_agencies:
            funding_agencies_data = funding_agencies()
            funding_agencies_data.funding_agency = 'European Agency (internal id: 1344862)'   
            funding_agencies_data.funding_agencies_cleanup()
            notice_data.funding_agencies.append(funding_agencies_data)
        else:
            pass
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__))
        pass

    try:
        est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde totale waarde")]//following::p[1]').text 
        est_amount = est_amount.split('btw:')[1].split('Munt:')[0]
        est_amount = est_amount.replace(' ','').replace(',','.')
        notice_data.est_amount = float(est_amount)
    except:
        try:
            est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text 
            est_amount = est_amount.replace(' ','')
            notice_data.est_amount = float(est_amount)
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

    try:
        grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde totale waarde")]//following::p[1]').text  
        grossbudgetlc = grossbudgetlc.split('btw:')[1].split('Munt:')[0]
        grossbudgetlc = grossbudgetlc.replace(' ','').replace(',','.')
        notice_data.grossbudgetlc = float(grossbudgetlc)
    except:
        try:
            grossbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Maximumwaarde van de raamovereenkomst")]//following::span[2]').text  
            grossbudgetlc = grossbudgetlc.replace(' ','').replace(',','.')
            notice_data.grossbudgetlc = float(grossbudgetlc)
            
        except Exception as e:
            logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
            pass
    
    notice_data.grossbudgeteuro = notice_data.grossbudgetlc   

    try:
        netbudgetlc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde exclusief btw")]//following::span[2]').text   
        netbudgetlc = netbudgetlc.replace(' ','')
        notice_data.netbudgetlc = float(netbudgetlc)
        
        notice_data.netbudgeteuro = notice_data.netbudgetlc 
    except Exception as e:
        logging.info("Exception in netbudgetlc: {}".format(type(e).__name__))
        pass

    try:
        time.sleep(3)
        Organisaties_clk = page_details.find_element(By.XPATH,'//*[contains(text(),"Organisaties")]')
        page_details.execute_script("arguments[0].click();",Organisaties_clk)
        time.sleep(5)
    except:
        pass

    customer_details_text = page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').text

    if 'Beschrijving' in customer_details_text:
        try:
            customer_details_text = customer_details_text.split('8. Organisaties')[1].split('Andere contactpunten:')[0]
        except:
            pass

        try:   
            customer_details_data = customer_details()
            try:
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Officiële benaming")]//following::dd[1]').text 
            except:
                customer_details_data.org_name = customer_details_text.split('Officiële naam:')[1].split('Registratienummer: ')[0].strip()

            try:
                customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Mailing address")]//following::dd[1]').text 
            except:
                try:
                    customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Postadres:")]//following::dd[1]').text
                except:
                    try:
                        customer_details_data.org_address = customer_details_text.split('Postadres:')[1].split('Stad:')[0].strip()
                    except Exception as e:
                        logging.info("Exception in org_address: {}".format(type(e).__name__))
                        pass

            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '//*[contains(text(),"Place")]//following::dd[1]').text  
            except:
                try:
                    customer_details_data.org_city = customer_details_text.split('Stad:')[1].split('Postcode:')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass

            customer_details_data.org_country = 'NL'
            customer_details_data.org_language = 'NL'

            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-mail")]//following::dd[1]').text
            except:
                try:
                    customer_details_data.org_email = customer_details_text.split('E-mail:')[1].split('Telefoon:')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contactpersoon")]//following::dd[1]').text  
            except:
                try:
                    customer_details_data.contact_person = customer_details_text.split('Contactpunt:')[1].split('E-mail:')[0].strip()
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telefoon")]//following::dd[1]').text 
            except:
                try:
                    customer_details_data.org_phone = customer_details_text.split('Telefoon:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Fax")]//following::dd[1]').text
            except:
                try:
                    customer_details_data.org_fax = customer_details_text.split('Fax:')[1].split('Internetadres:')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_fax: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS-code")]//following::dd[1]').text  
            except:
                try:
                    customer_details_data.customer_nuts =  customer_details_text.split('Onderverdeling land (NUTS):')[1].split('\n')[0].strip()  
                except Exception as e:
                    logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                    pass           

            try:
                customer_details_data.postal_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Postcode:")]//following::dd[1]').text  
            except:
                try:
                    customer_details_data.postal_code = customer_details_text.split('Postcode:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in postal_code: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoofdadres:")]//following::a[1]').text 
            except:
                try:
                    customer_details_data.org_website = customer_details_text.split('Internetadres:')[1].split('\n')[0].strip()
                except Exception as e:
                    logging.info("Exception in org_website: {}".format(type(e).__name__))
                    pass

            try:
                customer_details_data.customer_main_activity  = page_details.find_element(By.XPATH, '//*[contains(text(),"Activiteit van de aanbestedende dienst")]//following::td[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
                pass

            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)

        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass
            
    else:
        try:
            Organisaties_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Organisations")]')))
            Organisaties_clk =page_details.find_element(By.XPATH,'//*[contains(text(),"Organisations")]') 
            page_details.execute_script("arguments[0].click();",Organisaties_clk)
            time.sleep(5)

            customer_details_text = page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').text

            try:
                customer_details_text = customer_details_text.split('8. Organisations')[1].split('11. Notice information')[0]
            except:
                pass            

            customer_details_data = customer_details()
            customer_details_data.org_name = customer_details_text.split('Official name:')[1].split('\n')[0].strip()

            try:
                customer_details_data.org_address = customer_details_text.split('Postal address: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_city = customer_details_text.split('Town: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'NL'
            customer_details_data.org_language = 'NL'

            try:
                customer_details_data.org_email = customer_details_text.split('Email: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass        

            try:
                customer_details_data.contact_person = customer_details_text.split('Contact point: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass 

            try:
                customer_details_data.org_phone = customer_details_text.split('Telephone: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_fax = customer_details_text.split('Fax:')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in org_fax: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.postal_code = customer_details_text.split('Postcode: ')[1].split('\n')[0].strip()
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass            

            try:
                customer_details_data.org_website = customer_details_text.split('Internet address:')[1].split('\n')[0].strip()  
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass     
            
            try:
                customer_details_data.customer_main_activity  = page_details.find_element(By.XPATH, '//*[contains(text(),"Activity of the contracting authority")]//following::td[1]').text 
            except Exception as e:
                logging.info("Exception in customer_main_activity : {}".format(type(e).__name__))
                pass


            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)            
            
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

    try:
        try:
            Perceel_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Perceel")]')))  
            page_details.execute_script("arguments[0].click();",Perceel_clk)
            time.sleep(5)

            Perceel_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Perceel")])[2]')))  
            page_details.execute_script("arguments[0].click();",Perceel_clk)
            time.sleep(5)
        except:
            Deel_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[contains(text(),"Deel")])[4]')))  
            page_details.execute_script("arguments[0].click();",Deel_clk)
            time.sleep(5)

        try:              

            lots = page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').text
    
            if '5.1 Perceel:' in lots:
                lots = lots.split('5.1 Perceel:')
            elif '3.1 Deel:' in lots:
                lots = lots.split('3.1 Deel:')    

            lot_number = 1
            for single_record in lots[1:]:

                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number

                lot_details_data.lot_title = single_record.split("Titel:")[1].split('\n')[0]

                try:
                    lot_details_data.lot_description = single_record.split("Beschrijving:")[1].split('\n')[0]
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_actual_number = single_record.split('Titel:')[0].strip()
                except Exception as e:
                    logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_nuts = single_record.split('Onderverdeling land (NUTS):')[1].split('\n')[0]
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass

                try:
                    lot_netbudget_lc = single_record.split('Geraamde waarde exclusief btw:')[1].split('\n')[0]  
                    lot_netbudget_lc = re.sub("[^\d\.\,]","",lot_netbudget_lc)
                    lot_details_data.lot_netbudget_lc = float(lot_netbudget_lc.replace(',','').replace(' ','').strip())                
                except Exception as e:
                    logging.info("Exception in lot_netbudget_lc: {}".format(type(e).__name__))
                    pass
                
                try:
                    lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde")]//following::p[1]').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc).replace(' ','').replace(',','.').strip()
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc)
                except:
                    try:
                        lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Maximumwaarde van de raamovereenkomst")]//following::span[2]').text  
                        lot_grossbudget_lc = lot_grossbudget_lc.replace(' ','').replace(',','.')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass
                    
                lot_details_data.lot_grossbudgeteuro = lot_details_data.lot_grossbudget_lc
                
                try:
                    lot_details_data.lot_netbudget = lot_details_data.lot_netbudget_lc
                except Exception as e:
                    logging.info("Exception in lot_netbudget: {}".format(type(e).__name__))
                    pass

                try:
                    contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Aard van het contract")]//following::span[2]').text 
                    if 'Leveringen' in notice_data.contract_type_actual:
                        lot_details_data.contract_type = 'Supply'
                    elif 'Diensten' in contract_type:
                        lot_details_data.contract_type = 'Services'
                    elif 'Werken' in contract_type:
                        lot_details_data.contract_type = 'Works'

                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Aard van het contract")]//following::span[2]').text  
                except Exception as e:
                    logging.info("Exception in lot_contract_type_actual: {}".format(type(e).__name__))
                    pass

                try:
                    contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Begindatum")]//following::span[2]').text  
                    lot_details_data.contract_start_date  = datetime.strptime(contract_start_date, '%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')    
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass

                try:
                    contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Einddatum")]//following::span[2]').text    
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date, '%Y-%m-%d+%H:%M').strftime('%Y/%m/%d %H:%M:%S')
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_quantity = page_details.find_element(By.XPATH, '//*[contains(text(),"Hoeveelheid")]//following::span[2]').text  
                except Exception as e:
                    logging.info("Exception in lot_quantity: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd")]//following::td[1]').text  
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass        

                try:
                    lot_cpv_at_source = single_record.split('Belangrijkste classificatie (cpv):')[1].split('\n')[0]
                    lot_details_data.lot_cpv_at_source = re.findall("\d{8}",lot_cpv_at_source)[0]
                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpv_at_source = single_record.split('Aanvullende classificatie (cpv):')[1].split('\n')[0]
                    lot_cpv_at_sources = re.findall("\d{8}",lot_cpv_at_source)
                    lot_cpv_at_source = ''
                    for cpv1 in lot_cpv_at_sources:
                        lot_cpv_at_source += cpv1  
                        lot_cpv_at_source += ',' 
                    cpv_source = lot_cpv_at_source.rstrip(',')
                    lot_details_data.lot_cpv_at_source = lot_details_data.lot_cpv_at_source + ',' + cpv_source

                except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass    

                try:
                    lot_cpvs_data = lot_cpvs()

                    lot_cpv_code = single_record.split('Belangrijkste classificatie (cpv):')[1].split('\n')[0]
                    lot_cpvs_data.lot_cpv_code = re.findall("\d{8}",lot_cpv_code)[0]
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)

                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    lot_cpvs_data = lot_cpvs()

                    lot_cpv_code = single_record.split('Aanvullende classificatie (cpv):')[1].split('\n')[0]
                    lot_cpvs_data.lot_cpv_code = re.findall("\d{8}",lot_cpv_code)[0]
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:
                    lot_criteria_text_1 = single_record.split('5.1.10 Gunningscriteria')[1].split('5.1.11 Aanbestedingsstukken')[0]
                    lot_criteria_text_2 = lot_criteria_text_1.split('Criterium:')

                    for single_record_1 in lot_criteria_text_2[1:]:
                        lot_criteria_data = lot_criteria()

                        try:
                            lot_criteria_data.lot_criteria_weight = int(single_record_1.split('Gewicht (punten, exact):')[1].split('\n')[0])
                        except Exception as e:
                            logging.info("Exception in lot_criteria_weight: {}".format(type(e).__name__))
                            pass
                        
                        try:
                            lot_criteria_data.lot_criteria_title = single_record_1.split('Naam:')[1].split('\n')[0]

                            if 'Prijs' in lot_criteria_data.lot_criteria_title:
                                
                                if lot_criteria_data.lot_criteria_weight>=1:
                                
                                    lot_criteria_data.lot_is_price_related = True
                                else:
                                    lot_criteria_data.lot_is_price_related = False

                        except Exception as e:
                            logging.info("Exception in lot_criteria_title: {}".format(type(e).__name__))
                            pass   

                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)
                except Exception as e:
                    logging.info("Exception in lot_criteria: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass        
        
    except:
        try:        
            lots = page_details.find_element(By.CSS_SELECTOR, 'div.tap-content').text
            lots = lots.split('II.2) Beschrijving')
            for single_record_1 in lots[1:]:

                lot_title1 = single_record_1.split("II.2.2) Aanvullende CPV-code(s)")[0]
                lot_title2 = lot_title1.split("Benaming")[1].split("\n")[1]
                if len(lot_title2)< 5 and (lot_title2 =='-'):
                    continue
                lot_title = lot_title2            

                lot_details_data = lot_details()
                if lot_title is not None and lot_title !='':

                    lot_details_data.lot_title = lot_title
                    lot_title_english = GoogleTranslator(source='nl', target='en').translate(lot_details_data.lot_title)
                else:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                if 'Perceel nr' in lot_title1:
                    lot_actual_number = lot_title1.split('Perceel nr.:')[1].split("\n")[0]
                    lot_details_data.lot_actual_number = 'Perceel nr.:'+str(lot_actual_number)
                try:
                    lot_details_data.lot_number = int(lot_actual_number)
                except:
                    lot_details_data.lot_number = 1

                try:
                    lot_details_data.lot_description =  single_record_1.split('II.2.4) Beschrijving van de aanbesteding:')[1].split('II.2.5) Gunningscriteria')[0].strip()  
                except Exception as e:
                    logging.info("Exception in lot_description: {}".format(type(e).__name__))
                    pass

                try:
                    lot_details_data.lot_nuts =  single_record_1.split('NUTS-code:')[1].split('\n')[0]
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))      
                    pass

                try:
                    lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Geraamde waarde")]//following::p[1]').text
                    lot_grossbudget_lc = re.sub("[^\d\.\,]","",lot_grossbudget_lc).replace(' ','').replace(',','.').strip()
                    lot_details_data.lot_grossbudget_lc =float(lot_grossbudget_lc)
                except:
                    try:
                        lot_grossbudget_lc = page_details.find_element(By.XPATH, '//*[contains(text(),"Maximumwaarde van de raamovereenkomst")]//following::span[2]').text  
                        lot_grossbudget_lc = lot_grossbudget_lc.replace(' ','').replace(',','.')
                        lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass
                    
                lot_details_data.lot_grossbudgeteuro = lot_details_data.lot_grossbudget_lc

                try:
                    lot_details_data.contract_type = notice_data.notice_contract_type
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass

                try:
                    contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem")]//following::p[1]').text.split("Aanvang:")[1].split("\n")[0]
                    contract_start_date = re.findall('\d+/\d+/\d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')  
                except Exception as e:
                    logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
                    pass

                try:
                    contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Looptijd van de opdracht, de raamovereenkomst of het dynamische aankoopsysteem")]//following::p[1]').text.split("Einde:")[1].split("\n")[0]
                    contract_end_date = re.findall('\d+/\d+/\d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d/%m/%Y').strftime('%Y/%m/%d %H:%M:%S')  
                except Exception as e:
                    logging.info("Exception in contract_end_date: {}".format(type(e).__name__))
                    pass

                try:
                    for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div.tap-content'):
                        lot_cpvs_data = lot_cpvs()

                        lot_cpvs_data.lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Aanvullende CPV-code(s)")]//following::dd[1]').text.split("-")[0].strip() 

                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except Exception as e:
                    logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                    pass

                try:              
                    tender_criteria_text = single_record_1.split('II.2.5) Gunningscriteria')[1].split('II.2.6) Geraamde waarde')[0]

                    tender_criteria_data = tender_criteria()

                    tender_criteria_data.tender_criteria_title = tender_criteria_text.split('Naam')[1].split('\n')[0]    

                    try:
                        tender_criteria_data.tender_criteria_weight = int(tender_criteria_text.split('Weging:')[1].split('\n')[0]  )  
                    except Exception as e:
                        logging.info("Exception in tender_criteria_weight: {}".format(type(e).__name__))
                        pass

                    if 'Prijs' in tender_criteria_text:
                        tender_criteria_data.tender_is_price_related = True
                    else:
                        tender_criteria_data.tender_is_price_related = False

                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
                except Exception as e:
                    logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
                    pass

                try:
                    award_details_data = award_details()

                    award_details_data.bidder_name = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3)")]//following::dd[1]').text
                    award_details_data.address = page_details.find_element(By.XPATH, '//*[contains(text(),"V.2.3)")]//following::dd[3]').text

                    try:
                        initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over de waarde van de opdracht/het perceel")]//following::p[1]').text #.split("Aanvankelijk geraamde totale waarde van de opdracht/het perceel:")[1].split("\n")[1] 
                        initial_estimated_value = re.sub("[^\d\.\,]","",initial_estimated_value)
                        award_details_data.initial_estimated_value  =float(initial_estimated_value.replace(',','').replace(' ','').strip())
                    except:
                        pass
                    try:
                        grossawardvaluelc = page_details.find_element(By.XPATH, '//*[contains(text(),"Inlichtingen over de waarde van de opdracht/het perceel")]//following::p[2]').text #.split("Totale waarde van de opdracht/het perceel:")[1].split("\n")[1]
                        grossawardvaluelc = re.sub("[^\d\.\,]","",grossawardvaluelc)
                        award_details_data.grossawardvaluelc  =float(grossawardvaluelc.replace(',','').replace(' ','').strip())
                    except:
                        pass

                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in award_details: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass
    
    try:
        try:              
            attachments_data = attachments()

            attachments_data.file_name = 'Download PDF'
            attachments_data.file_type = 'PDF'
            external_url = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-tab-content-0-1"]/div/tn-aankondiging-publicatie-tab/tn-secondary-button/div/button'))) 
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments_1: {}".format(type(e).__name__)) 
            pass   

        try:      
            Documenten_clk = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[contains(text(),"Documenten")]')))  
            page_details.execute_script("arguments[0].click();",Documenten_clk)
            time.sleep(5)

            attachments_data = attachments()
            attachments_data.file_name = 'Tender Documents'
            attachments_data.file_type = '.zip'

            external_url = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mat-tab-content-0-2"]/div/tn-aankondiging-documenten-tab/div/tn-secondary-button/div/button'))) 
            page_details.execute_script("arguments[0].click();",external_url)
            time.sleep(5)
            file_dwn = Doc_Download.file_download()
            attachments_data.external_url = str(file_dwn[0]) 

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)

        except Exception as e:
            logging.info("Exception in attachments_2: {}".format(type(e).__name__)) 
            pass
    
    except Exception as e:
        logging.info("Exception in attachments_: {}".format(type(e).__name__)) 
        pass    
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title) 
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']

options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome(options=options)
page_details = Doc_Download.page_details

try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://www.tenderned.nl/aankondigingen/overzicht"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        Publication_type = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'/html/body/tn-root/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer/div/tn-aankondiging-filter/div[2]/tn-publicatie-type-selector/tn-form-input-multiple-select/mat-form-field/div[1]/div[2]/div/mat-select/div/div[2]')))
        page_main.execute_script("arguments[0].click();",Publication_type)
        time.sleep(2)

        Marktconsultatie_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="mat-pseudo-checkbox mat-mdc-option-pseudo-checkbox mat-pseudo-checkbox-full ng-star-inserted"])[1]')))
        page_main.execute_script("arguments[0].click();",Marktconsultatie_click)
        time.sleep(2)
        
        Aankondiging_opdracht_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="mat-pseudo-checkbox mat-mdc-option-pseudo-checkbox mat-pseudo-checkbox-full ng-star-inserted"])[2]')))
        page_main.execute_script("arguments[0].click();",Aankondiging_opdracht_click)
        time.sleep(2)
        
        Rectificatie_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="mat-pseudo-checkbox mat-mdc-option-pseudo-checkbox mat-pseudo-checkbox-full ng-star-inserted"])[2]')))
        page_main.execute_script("arguments[0].click();",Rectificatie_click)
        time.sleep(2)
        
        Aankondiging_van_een_wijziging_click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'(//*[@class="mat-pseudo-checkbox mat-mdc-option-pseudo-checkbox mat-pseudo-checkbox-full ng-star-inserted"])[3]')))
        page_main.execute_script("arguments[0].click();",Aankondiging_van_een_wijziging_click)  
        time.sleep(5)
        
        try:
            for page_no in range(2,6):
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))
                length = len(rows)
                Laad_meer_clk = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/div[4]/tn-secondary-button/div/button')))  
                page_main.execute_script("arguments[0].click();",Laad_meer_clk)
                
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/tn-aankondigingen-page/div[2]/div/tn-aankondiging-overzicht/mat-drawer-container/mat-drawer-content/div[2]/div[2]/mat-card')))[records]
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
    page_details.quit() 
    
    output_json_file.copyFinalJSONToServer(output_json_folder)