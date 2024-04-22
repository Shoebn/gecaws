from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "no_doffin_amd"
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
SCRIPT_NAME = "no_doffin_amd"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    notice_data.main_language = 'NO'
    notice_data.currency = 'NOK'
    
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'NO'
    notice_data.performance_country.append(performance_country_data)
    
    notice_data.procurement_method = 2
    notice_data.script_name = "no_doffin_amd"
    
    notice_data.notice_type = 16
          
    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'h2.NoticeCard_title__ukzjK').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass 
    
    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " div.NoticeCard_bottom_line__u61Hb > p.NoticeCard_issue_date__Dlug\+").text
        publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)  
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
        
    try:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#mainContent').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '(//*[contains(text(),"Referanse")])[1]//following::dd[1]').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.local_description = page_details.find_element(By.CSS_SELECTOR, 'p.Noticepage_content_section_description__sVPDe').text
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR," section > details:nth-child(2) > summary > svg").click()
        time.sleep(3)
    except:
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"  section > details:nth-child(1) > summary > svg").click()
        time.sleep(3)
    except:
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"section > details:nth-child(3) > summary > svg").click()
        time.sleep(3)
    except:
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"section > details:nth-child(4) > summary > svg").click()
        time.sleep(3)
    except:
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"section > details:nth-child(5) > summary > svg").click()
        time.sleep(3)
    except:
        pass
    
    try:
        clk1 = page_details.find_element(By.CSS_SELECTOR,"section > details:nth-child(6) > summary > svg").click()
        time.sleep(3)
    except:
        pass
    
    try:
        est_amount = page_details.find_element(By.XPATH, '(//*[contains(text(),"Anslått verdi eksklusiv merverdiavgift")])[1]//following::p[1]').text
        est_amount = re.sub("[^\d\.\,]","",est_amount)
        notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
        notice_data.netbudgetlc = notice_data.est_amount
    except:
        try:
            est_amount = page_details.find_element(By.XPATH, '(//*[contains(text(),"Estimated value excluding VAT")])[1]//following::p[1]').text
            est_amount = re.sub("[^\d\.\,]","",est_amount)
            notice_data.est_amount =float(est_amount.replace('.','').replace(',','').strip())
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '(//*[contains(text(),"Kontraktens art")])[1]//following::p[1]').text
        if 'Konstruksjon' in notice_data.contract_type_actual or "Bygge- og anleggsarbeid" in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        elif 'Varer' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Tjenester' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
    except:
        try:
            notice_data.contract_type_actual = page_details.find_element(By.XPATH, '(//*[contains(text(),"Nature of the contract")])[1]//following::p[1]').text
            if 'Construction' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Works'
            elif 'Items' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Supply'
            elif 'Services' in notice_data.contract_type_actual:
                notice_data.notice_contract_type = 'Service'
        except Exception as e:
            logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
            pass
        
    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '(//*[contains(text(),"Varighet")])[1]//following::p[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
        
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Adresse på anskaffelsesdokumentene')]//following::section[1]").text
    except:
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, "//*[contains(text(),'Buyer profile')]//following::section[1]").text
        except Exception as e:
            logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
            pass
        
    try:  
        document_opening_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Dato/klokkeslett')]//following::section[1]").text
        document_opening_time = re.findall('\d+.\d+.\d{4}',document_opening_time)[0]
        notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
        logging.info(notice_data.document_opening_time)
    except:
        try:
            document_opening_time = page_details.find_element(By.XPATH, "//*[contains(text(),'Date/time')]//following::section[1]").text
            document_opening_time = re.findall('\d+.\d+.\d{4}',document_opening_time)[0]
            notice_data.document_opening_time = datetime.strptime(document_opening_time,'%d.%m.%Y').strftime('%Y-%m-%d')
            logging.info(notice_data.document_opening_time)
        except Exception as e:
            logging.info("Exception in document_opening_time: {}".format(type(e).__name__))
            pass
            
    try:              
        customer_details_data = customer_details()
        # Onsite Field -Organization
        # Onsite Comment -None

        customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, ' div.NoticeCard_header__Wg1\+c > p').text
        
        try:
            postal_code = page_details.find_element(By.XPATH, '(//*[contains(text(),"Postnummer")])[1]//following::p[1]').text
            customer_details_data.postal_code = re.sub("[^\d\.\,]", "", postal_code)
        except:
            try:
                postal_code = page_details.find_element(By.XPATH, '(//*[contains(text(),"Postcode")])[1]//following::p[1]').text
                customer_details_data.postal_code = re.sub("[^\d\.\,]", "", postal_code)
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass
        
        try:
            customer_details_data.org_city = page_details.find_element(By.XPATH, '(//*[contains(text(),"By")])[1]//following::p[1]').text
        except:
            try:
                customer_details_data.org_city = page_details.find_element(By.XPATH, '(//*[contains(text(),"Town")])[1]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_city: {}".format(type(e).__name__))
                pass
        
        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Contact point")])[1]//following::p[1]').text
        except:
            try:
                customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Kontaktpunkt")])[1]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass
            
        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"E-post")])[1]//following::p[1]').text
        except:
            try:
                customer_details_data.org_email = page_details.find_element(By.XPATH, '(//*[contains(text(),"Email")])[1]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass
            
        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"Telefon")])[1]//following::p[1]').text
        except:
            try:
                customer_details_data.org_phone = page_details.find_element(By.XPATH, '(//*[contains(text(),"Telephone")])[1]//following::p[1]').text
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass
            
        try:
            customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Hovedaktivitet")]//following::dd[1]').text
        except:
            try:
                customer_details_data.customer_main_activity = page_details.find_element(By.XPATH, '//*[contains(text(),"Main activity")]//following::dd[1]').text
            except Exception as e:
                logging.info("Exception in customer_main_activity: {}".format(type(e).__name__))
                pass
        
        
        customer_details_data.org_country = 'NO'
        customer_details_data.org_language = 'NO'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
    try:
        notice_data.document_type_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Type skjema")])[1]//following::p[1]').text
    except:
        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, "(//*[contains(text(),'Form type')])[1]//following::p[1]").text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass
        
    try:
        dispatch_date = page_details.find_element(By.XPATH, '(//*[contains(text(),"Varsel utsendelsesdato")])[1]//following::p[1]').text
        dispatch_date = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',dispatch_date)[0]
        notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
    except:
        try:
            dispatch_date = page_details.find_element(By.XPATH, '(//*[contains(text(),"Notice dispatch date")])[1]//following::p[1]').text
            dispatch_date = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',dispatch_date)[0]
            notice_data.dispatch_date = datetime.strptime(dispatch_date,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in dispatch_date: {}".format(type(e).__name__))
            pass
    
    try:
        category_list=''
        for category_data in page_details.find_elements(By.CSS_SELECTOR, ' li > a > p'):
            category_data = category_data.text.strip()
            category_data = GoogleTranslator(source='auto', target='en').translate(category_data)
            category = category_data.lower()
            cpv_codes = fn.CPV_mapping("assets/no_doffin_category_cpv.csv",category)

            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)

            category_list += category
            category_list += ','
        notice_data.category =category_list.rstrip(',')
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
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
    threshold = th.strftime('%Y/%m/%d %H:%M:%S')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.doffin.no/search?page=1&status=CANCELLED&type=ANNOUNCEMENT_OF_COMPETITION'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(1,4):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/div/main/div[2]/section/ul/li'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/main/div[2]/section/ul/li')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div/main/div[2]/section/ul/li')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
                        
                if notice_data.notice_deadline is not None and notice_data.notice_deadline < threshold:
                    break
                        
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="mainContent"]/div[2]/section/nav/ul/li[6]/button')))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/div/main/div[2]/section/ul/li'),page_check))
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
