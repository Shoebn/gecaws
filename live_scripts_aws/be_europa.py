from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "be_europa"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "be_europa"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.script_name = 'be_europa'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -Places of delivery or performance
    # Onsite Comment -if performance_country is not available in "Places of delivery or performance" field then paas "Belgium" country

    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'EUR'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 4
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-title').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-subtitle > span').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -None
    # Onsite Comment -None

    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'eui-card-header-right-content > div > eui-chip').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass


    try:
        notice_url = WebDriverWait(tender_html_element, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"eui-card-header-title > a > strong")))
        notice_url.location_once_scrolled_into_view
        notice_url.click()
        notice_data.notice_url = page_main.current_url
        time.sleep(15)
        logging.info(notice_data.notice_url)
    except Exception as e:
        pass
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url   
    

    WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[1]/eui-card/mat-card/eui-card-content/mat-card-content/div[1]/div[1]/div[1]'))).text

    # Onsite Field -Publication date
    # Onsite Comment -for publish_Date click on "div.eui-card-header__expander"  button and grab data from "Publication date "
    try:
        publish_date = page_main.find_element(By.XPATH, "//*[contains(text(),'TED publication date')]//following::div[1]").text
        publish_date = re.findall('\d+ \w+ \d{4}',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return
    
#     # Onsite Field -Deadline date
#     # Onsite Comment -for Deadline date  click on "div.eui-card-header__expander"  button and grab data from "Deadline date"
    try:
        try:
            notice_deadline = page_main.find_element(By.XPATH, "//*[contains(text(),'Time limit for receipt of tenders')]//following::div[1]").text
        except:
            notice_deadline = page_main.find_element(By.XPATH, "//*[contains(text(),'Time limit for requests to participate')]//following::div[1]").text
        notice_deadline = re.findall('\d+ \w+ \d{4}',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.notice_deadline)
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Contract type
#     # Onsite Comment -for notice_contract_type  click on "div.eui-card-header__expander"  button and grab data from "Contract type"  ,    Replace following keywords with given respective keywords  ('Services = service' , 'Supplies = supply' , 'Works = Works')

    try:
        notice_data.contract_type_actual = page_main.find_element(By.XPATH, "//*[contains(text(),'Contract type')]//following::div[1]").text
        if 'Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Service'
        elif 'Supplies' in notice_data.contract_type_actual: 
            notice_data.notice_contract_type = 'Supply'  
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works' 
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass


    
#     # Onsite Field -None
#     # Onsite Comment -None
    try:
        notice_data.notice_text += page_main.find_element(By.CSS_SELECTOR, 'body > sedia-opportunities-v10 > ng-component > eui-page > eui-page-content > eui-page-columns > eui-page-column:nth-child(2)').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
    try:
        notice_data.local_description = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::mat-card-content[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
     
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'BE'
    notice_data.performance_country.append(performance_country_data)

    
#     # Onsite Field -Description
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_main.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::mat-card-content[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -None
#     # Onsite Comment -None
    notice_data.class_at_source = "CPV"
    
# Onsite Field -Main CPV code
# Onsite Comment -ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"
    try:              
# Onsite Field -Main CPV code
# Onsite Comment -ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"
        try:
            cpvs_data = cpvs()
            cpv_code = page_main.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::div[1]').text
            cpvs_data.cpv_code = re.findall("\d{8}",cpv_code)[0]
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpv_code: {}".format(type(e).__name__))
            pass
        try:
            text1=page_main.find_element(By.CSS_SELECTOR,'body > sedia-opportunities-v10 > ng-component > eui-page > eui-page-content > eui-page-columns > eui-page-column:nth-child(2) > div > eui-page-column-body > div:nth-child(1) > eui-card > mat-card > eui-card-content > mat-card-content').text
            cpv_code1 = fn.get_string_between(text1,'Additional CPV code','Places of delivery or performance')
            cpv_code1 = re.findall("\d{8}",cpv_code1)
            for cpv1 in cpv_code1:
                cpvs_data = cpvs()
                cpvs_data.cpv_code=cpv1
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)     
        except:
            pass
        
    except Exception as e:
        logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
        pass
    
    try:
        cpv_source = page_main.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::div[1]').text
        notice_data.cpv_at_source = re.findall("\d{8}",cpv_source)[0]
    except:
        pass
    
    try:
        text1=page_main.find_element(By.CSS_SELECTOR,'body > sedia-opportunities-v10 > ng-component > eui-page > eui-page-content > eui-page-columns > eui-page-column:nth-child(2) > div > eui-page-column-body > div:nth-child(1) > eui-card > mat-card > eui-card-content > mat-card-content > div:nth-child(4) > div').text
        if 'Additional CPV code' in text1 :
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
    
# # Onsite Field -None
# # Onsite Comment -EUROPEAN UNION (EU)

    try:              
        funding_agencies_data = funding_agencies()
        funding_agencies_data.funding_agency = '1344862'
        funding_agencies_data.funding_agencies_cleanup()
        notice_data.funding_agencies.append(funding_agencies_data)
    except Exception as e:
        logging.info("Exception in funding_agencies: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = 'EUROPEAN UNION (EU)'
    # Onsite Field -None
    # Onsite Comment -if performance_country is not available in "Places of delivery or performance" field then paas "Belgium" country , ref_url : "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/tender-details/14766en?grants=false&forthcoming=false&closed=false&pageNumber=3"

        customer_details_data.org_country = 'BE'
    

        customer_details_data.org_language = 'EN'
        customer_details_data.org_parent_id = '7314301'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# Onsite Field -None
# Onsite Comment -None

    try:
        lot_number=1  
        for single_record in page_main.find_elements(By.CSS_SELECTOR, 'body > sedia-opportunities-v10 > ng-component > eui-page > eui-page-content > eui-page-columns > eui-page-column:nth-child(2) > div > eui-page-column-body > div:nth-child(2) > eui-card > mat-card div.mb-4'):
               
                
    #         # Onsite Field -Lots
    #         # Onsite Comment -split only lot_title  for ex."AO-06A50/2015/M013 — Framework contract for works with maintenance services in the field of centralised technical management for European Parliament buildings in Brussels" , here split only "Framework contract for works with maintenance services in the field of centralised technical management for European Parliament buildings in Brussels"

                lot_title = single_record.find_element(By.CSS_SELECTOR, 'strong').text
                if lot_title !='':
                    lot_details_data = lot_details()
                    lot_details_data.lot_title = lot_title
                    lot_details_data.lot_number = lot_number
                    lot_details_data.lot_title_english = lot_details_data.lot_title

                    try:
                        lot_cpvs_data = lot_cpvs()

                        lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(n) > div.row.mt-3.ng-star-inserted > div:nth-child(1) > div.ng-star-inserted').text
                        lot_cpvs_data.lot_cpv_code = re.sub("[^\d]","",lot_cpv_code)
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    except Exception as e:
                        logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                        pass


                    try:
                        lot_details_data.lot_contract_type_actual= page_main.find_element(By.XPATH, "//*[contains(text(),'Contract type')]//following::div[1]").text
                        if 'Services' in lot_details_data.lot_contract_type_actual:
                             lot_details_data.contract_type = 'Service'
                        elif 'Supplies' in lot_details_data.lot_contract_type_actual: 
                             lot_details_data.contract_type = 'Supply'  
                        elif 'Works' in lot_details_data.lot_contract_type_actual:
                             lot_details_data.contract_type = 'Works' 
                        else:
                            pass
                    except Exception as e:
                        logging.info("Exception in lot_contract_type: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_cpv_at_source = ''
                        lot_cpv_at_source = single_record.find_element(By.CSS_SELECTOR, ' div:nth-child(n) > div.row.mt-3.ng-star-inserted > div:nth-child(1) > div.ng-star-inserted').text.split('-')[0]
                        lot_details_data.lot_cpv_at_source = re.sub("[^\d]","",lot_cpv_at_source)
                        notice_data.cpv_at_source += ','
                        notice_data.cpv_at_source += lot_details_data.lot_cpv_at_source
                    except:
                        pass 

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number +=1
    except Exception as e:
        logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
        pass

        
#     # Onsite Field -Call for tenders' details
#     # Onsite Comment -None

    try:
        notice_data.additional_tender_url = page_main.find_element(By.CSS_SELECTOR, 'a.ng-star-inserted').get_attribute('href')
    except Exception as e:
        logging.info("Exception in additional_tender_url: {}".format(type(e).__name__))
        pass
    
    clk=page_main.find_element(By.XPATH,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[1]/div[2]/eui-page-column-body/a/span').click()
    time.sleep(15)
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
    duplicate_check_data = fn.duplicate_check_data_from_previous_scraping(SCRIPT_NAME,MAX_NOTICES_DUPLICATE,notice_data.identifier,previous_scraping_log_check)
    NOTICE_DUPLICATE_COUNT = duplicate_check_data[1]
    if duplicate_check_data[0] == False:
        return
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
    urls = ["https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search?grants=false&forthcoming=false&closed=false"] 
    for url in urls:
        fn.load_page_expect_xpath(page_main, url,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td', 50)
        logging.info('----------------------------------')
        logging.info(url)
       
        try:
            clk=page_main.find_element(By.CSS_SELECTOR,'#cookie-consent-banner > div > div > div.cck-actions.wt-noconflict > a:nth-child(1)').click()
        except:
            pass
        
        try:
            page_main.switch_to.frame(0)
        except:
            pass
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break

                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break

                    if NOTICE_DUPLICATE_COUNT >= MAX_NOTICES_DUPLICATE:
                        logging.info("NOTICES_DUPLICATE::", MAX_NOTICES_DUPLICATE)
                        break

                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break

                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.LINK_TEXT,str(page_no))))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/sedia-opportunities-v10/ng-component/eui-page/eui-page-content/eui-page-columns/eui-page-column[2]/div/eui-page-column-body/div[2]/table/tbody/tr/td'),page_check))
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