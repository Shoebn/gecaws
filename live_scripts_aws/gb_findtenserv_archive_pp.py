from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gb_findtenserv_archive_pp"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "gb_findtenserv_archive_pp"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'gb_findtenserv_archive_pp'
    
    notice_data.main_language = 'EN'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.currency = 'GBP'
    
    notice_data.procurement_method = 2
    
    notice_data.notice_type = 3


    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > dd').text.split(":")[1].strip()
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass

    try:
        publish_date = tender_html_element.text.split("Publication date")[1].strip()
        publish_date = re.findall('\d+ \w+ \d{4}, \d+:\d{2}[apAP][mM]',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
 
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main-container > div.govuk-width-container > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    page_details_text = page_details.find_element(By.XPATH, '//*[@id="main-content"]').text
    
    try:
        local_description_half = page_details.find_element(By.XPATH, '(//span[contains(text(),"Description of the procurement")])[2]').text
        local_desc_split_till = page_details.find_element(By.XPATH, '(//span[contains(text(),"Description of the procurement")])[2]//following::span[2]').text
        local_description1 = page_details_text.split(local_description_half)[1].split(local_desc_split_till)[0].strip()
    except:
        try:
            local_description_half1 = page_details.find_element(By.XPATH, '(//h3[contains(text(),"Description")])[1]').text
            local_desc_split_till1 = page_details.find_element(By.XPATH, '(//h3[contains(text(),"Description")])[1]//following::h3').text
            local_description13= page_details_text.split(local_description_half1)[1].split(local_desc_split_till1)[0].strip()
        except Exception as e:
            logging.info("Exception in local_description1: {}".format(type(e).__name__))
            pass 
    
    try:
        local_description_2half = page_details.find_element(By.XPATH, '(//span[contains(text(),"Short description")])[2]').text
        local_desc_split_till2 = page_details.find_element(By.XPATH, '(//span[contains(text(),"Short description")])[2]//following::span[2]').text
        local_description2 = page_details_text.split(local_description_2half)[1].split(local_desc_split_till2)[0].strip()
    except:
        try:
            local_description_half1 = page_details.find_element(By.XPATH, '(//h3[contains(text(),"Description")])[1]').text
            local_desc_split_till1 = page_details.find_element(By.XPATH, '(//h3[contains(text(),"Description")])[1]//following::h3').text
            local_description3 = page_details_text.split(local_description_half1)[1].split(local_desc_split_till1)[0].strip()
        except Exception as e:
            logging.info("Exception in local_description1: {}".format(type(e).__name__))
            pass 
    
    try:
        notice_data.local_description = local_description2+'\n'+local_description1
        notice_data.notice_summary_english = notice_data.local_description
    except:
        try:
            notice_data.local_description = local_description3
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
    # Onsite Field -Reference
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference")]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.CSS_SELECTOR, ' div.govuk-grid-column-three-quarters.break-word > p:nth-child(3)').text.split("Notice reference: ")[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract type
    # Onsite Comment -Replace follwing keywords with given respective kywords ('Service contract = services','Works = works',' Supply contract = supply ')

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p[1]').text
        if "Services" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Goods" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Supply contract" in notice_data.contract_type_actual or "Supplies" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Supply"
        elif "Service contract" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Service"
        elif "Works" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = "Works"
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Closing date")]//following::p[1]').text
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
    try:
        est_amount_data = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.5) Estimated total value")]//following::p[1]').text
        est_amount = re.sub("[^\d\.\,]", "", est_amount_data)
        notice_data.est_amount = float(est_amount.replace(',','').strip())
        if "excluding VAT:" in est_amount_data:
            notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.contract_duration = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text.split('Duration in months\n')[1].split('\n')[0]
        notice_data.contract_duration = 'Duration in months:  ' + notice_data.contract_duration
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
    try:
        additional_tender_url_data = page_details.find_element(By.XPATH,'//*[contains(text(),"VI.3) Additional information")]//following::a[1]').text
        if "Back to top" in additional_tender_url_data:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH,'//*[contains(text(),"Main address")]//following::a[1]').text.split('"')[0].strip()
        else:
            notice_data.additional_tender_url = additional_tender_url_data.split('"')[0].strip()
    except:
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH,'//*[contains(text(),"Main address")]//following::a[1]').text.split('"')[0].strip()
        except:
            pass
        

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
      
        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result > div:nth-child(2)').text
        
        # Onsite Field -2. Buyer
        # Onsite Comment -take only address from the given selector

        try:
            org_address = page_details.find_element(By.CSS_SELECTOR, '#main-container > div.govuk-width-container > main').text.split("I.1) Name and addresses")[1].split("Contact")[0].split("Email")[0].strip()
            customer_details_data.org_address = org_address.replace(customer_details_data.org_name,'').strip()
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Contract location
#         # Onsite Comment -None

        try:
            customer_details_data.org_city = page_details.find_element(By.CSS_SELECTOR, ' div:nth-child(2) > p:nth-child(5)').text
        except Exception as e:
            logging.info("Exception in org_city: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Contact name:
        # Onsite Comment -split contact_person from the given selector

        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::p[1]').text
            if "Notices are based on" in contact_person:
                pass
            else:
                customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Telephone
        # Onsite Comment -split org_phone from the given selector

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass
        
#         # Onsite Field -Email:
#         # Onsite Comment -split org_email from the given selector
        try:
            org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Email")])[2]').text
            if ':' in org_email:
                customer_details_data.org_email = org_email.split(':')[1].split('\n')[0].strip()
            else:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '((//*[contains(text(),"Email")])[2]//following::p)[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -NUTS code:
        # Onsite Comment -split customer_nuts from the given selector

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        
        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass
        
        # Onsite Field -Website:
        # Onsite Comment -None

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
        
        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text.split('Main activity')[1].split('Section II: Object')[0].strip()
        except:
            pass
        
        try:
            customer_details_data.type_of_authority_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of the contracting authority")]//following::p[1]').text
        except Exception as e:
            logging.info("Exception in type_of_authority_code: {}".format(type(e).__name__))
            pass
        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass

    notice_data.class_at_source = 'CPV'
    
    try:
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text
        cpv_code = cpv_code.split('-')[0].strip()
        cpvs_data = cpvs()
        cpvs_data.cpv_code = cpv_code
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_code+','
    except:
        pass
    
    text1 = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text
    try:
        cpv1  =fn.get_string_between(text1,'II.2.2) Additional CPV code(s)','II.2.3) Place of performance')
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

    
    try:
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main category (CPV code)")]//following::ul[1]').text
        cpv_code = cpv_code.split('-')[0].strip()
        cpvs_data = cpvs()
        cpvs_data.cpv_code = cpv_code
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
        notice_data.cpv_at_source = cpv_code+','
    except:  
        pass

    
    try:
        cpv2  =fn.get_string_between(text1,'Additional categories (CPV codes)','Contract location')
        cpv_regex2 = re.compile(r'\d{8}')
        lot_cpvs_dataa2 = cpv_regex2.findall(cpv2)
        for cpv in lot_cpvs_dataa2:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
            notice_data.cpv_at_source += cpv
            notice_data.cpv_at_source += ','
        notice_data.cpv_at_source = notice_data.cpv_at_source.rstrip(',')
    except:
        pass

    try:
        text1 = page_details.find_element(By.CSS_SELECTOR,'div#main-content').text
        if "This contract is divided into lots: Yes" in text1:
            lot_deatils = text1.split('II.2) Description')
            lot_number = 1
            for lot in lot_deatils:
                if 'Lot No' in lot:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    lot_actual_number = lot.split("Lot No\n")[1].split('\n')[0]
                    lot_details_data.lot_actual_number = 'Lot No '+ lot_actual_number 

                    lot_details_data.lot_title = lot.split("Title\n")[1].split('\n')[0]
                    lot_details_data.lot_title_english = lot_details_data.lot_title

                    if len(lot_details_data.lot_title) == 6:
                        lot_details_data.lot_title =  lot_details_data.lot_actual_number
                    try:
                        lot_description1 = page_details.find_element(By.XPATH, '(//span[contains(text(),"Description of the procurement")])[2]').text
                        lot_description2 = page_details.find_element(By.XPATH, '(//span[contains(text(),"Description of the procurement")])[2]//following::span[2]').text
                        lot_details_data.lot_description = page_details_text.split(lot_description1)[1].split(lot_description2)[0].strip()
                        lot_details_data.lot_description_english = lot_details_data.lot_description
                    except:
                        pass

                    try:
                        contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract end date (estimated)")]//following::p[1]').text
                        contract_end_date = re.findall('\d+ \w+ \d{4}',contract_end_date)[0]
                        lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass

                    try:
                        contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract start date (estimated)")]//following::p[1]').text
                        contract_start_date = re.findall('\d+ \w+ \d{4}',contract_start_date)[0]
                        lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                    except:
                        pass


                    try:
                        lot_nuts = lot.split('NUTS codes\n')[1].split("Main site or place of performance")[0].split('II.2.4) Description of the procurement')[0].strip()
                        lot_nuts = lot_nuts.splitlines()
                        lot_nuts = ','.join(lot_nuts)
                        lot_details_data.lot_nuts  = lot_nuts.lstrip(',')
                    except:
                        pass

                    try:
                        lot_netbudget_lc_data = page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.6) Estimated value")]//following::p[1]').text
                        lot_netbudget_lc = re.sub("[^\d\.\,]", "", lot_netbudget_lc_data)
                        lot_netbudget_lc = float(lot_netbudget_lc.replace(',','').strip())
                        if "excluding VAT:" in lot_netbudget_lc_data:
                            lot_details_data.lot_netbudget_lc = lot_netbudget_lc
                    except Exception as e:
                        logging.info("Exception in grossbudgetlc: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual
                        lot_details_data.contract_type = notice_data.notice_contract_type
                    except Exception as e:
                        logging.info("Exception in contract_type: {}".format(type(e).__name__))
                        pass

                    try:
                        cpv = fn.get_string_between(lot, 'II.2.2) Additional CPV code(s)', 'II.2.3) Place of performance')
                        cpv_regex = re.compile(r'\d{8}')
                        lot_cpvs_dataa = cpv_regex.findall(cpv)
                        for cpv in lot_cpvs_dataa:
                            lot_cpvs_data = lot_cpvs()
                            lot_cpvs_data.lot_cpv_code = cpv
                            lot_cpvs_data.lot_cpvs_cleanup()
                            lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    except:
                        pass

                    try:
                        cpv = fn.get_string_between(lot, 'II.2.2) Additional CPV code(s)', 'II.2.3) Place of performance')
                        cpv_regex = re.compile(r'\d{8}')
                        lot_cpvs_dataa = cpv_regex.findall(cpv)
                        lot_cpv_at_source = ''
                        for cpv in lot_cpvs_dataa:
                            lot_cpv_at_source += cpv
                            lot_cpv_at_source += ','
                        lot_details_data.lot_cpv_at_source = lot_cpv_at_source.rstrip(',')

                    except:
                        pass
                    if lot_details_data.lot_title != None:
                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details1: {}".format(type(e).__name__)) 
        pass
    
    try:
        lot_deatils1 = page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text.split('II.1.6) Information about lots')[1].split("II.2) Description")[0]
        lot_number = 1
        for lot in lot_deatils1.split('\n'):
            if "Lot" in lot:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                lot_details_data.lot_title = lot.split(":")[1]
                lot_details_data.lot_title_english = lot_details_data.lot_title
                
                if lot_details_data.lot_title != None:
                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details2: {}".format(type(e).__name__)) 
        pass
    
    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#view-notice-side-menu > div:nth-child(2) > ul > li '):
            attachments_data = attachments()
            attachments_data.file_name = 'Download'
            attachments_data.external_url = single_record.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            # Onsite Field -Download
            # Onsite Comment -split file_type from the given selector
            try:
                attachments_data.file_type = single_record.find_element(By.CSS_SELECTOR, 'a').text.split("version")[0]
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass
        
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
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver(arguments) 
page_details = fn.init_chrome_driver(arguments) 
try:
    th = '01/01/2022'
    th1 = '28/12/2023'
    logging.info("Scraping from or greater than: " + th)
    urls = ['https://www.find-tender.service.gov.uk/Search/Results'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        time.sleep(10)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#stage\[2\]_label")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#stage\[3\]_label")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)
        
        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#daterange_id > button")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(2)

        fromday =  page_main.find_element(By.ID,"published_date_from-day")
        fromday.clear()
        fromth = th.split('/')[0]
        fromday.send_keys(fromth)
        
        frommnth =  page_main.find_element(By.ID,"published_date_from-month")
        frommnth.clear()
        fromth = th.split('/')[1]
        frommnth.send_keys(fromth)
        
        fromyr =  page_main.find_element(By.ID,"published_date_from-year")
        fromyr.clear()
        fromth = th.split('/')[2]
        fromyr.send_keys(fromth)


        to_day =  page_main.find_element(By.ID,"published_date_to-day")
        to_day.clear()
        toth = th1.split('/')[0]
        to_day.send_keys(toth)
        
        tomnth =  page_main.find_element(By.ID,"published_date_to-month")
        tomnth.clear()
        toth = th1.split('/')[1]
        tomnth.send_keys(toth)
        
        toyr =  page_main.find_element(By.ID,"published_date_to-year")
        toyr.clear()
        toth = th1.split('/')[2]
        toyr.send_keys(toth)

        click = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#adv_search_button")))
        page_main.execute_script("arguments[0].click();",click)
        time.sleep(3)
        
        try:
            WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#dashboard_notices > div.gadget-body > div:nth-child(1)')))
        except:
            pass
            
        for page_no in range(356,500):
            url = 'https://www.find-tender.service.gov.uk/Search/Results?&page='+str(page_no)+'#dashboard_notices'
            fn.load_page(page_main, url, 50)
            logging.info(url)
            page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div'))).text
            rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="dashboard_notices"]/div[1]/div')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break

                if notice_count == 50:
                    output_json_file.copyFinalJSONToServer(output_json_folder)
                    output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
                    notice_count = 0
    logging.info("Finished processing. Scraped {} notices".format(tnotice_count))
except Exception as e:
    raise e
    logging.info("Exception:"+str(e))
finally:
    page_main.quit()
    page_details.quit() 
    output_json_file.copyFinalJSONToServer(output_json_folder)
