from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_sa_ca"
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
import gec_common.Doc_Download
from selenium.webdriver.chrome.options import Options

# Note:Open the site than click on "CONTRACTS" dropdown button than second click "Across Government Contracts" in dropdown button than grab the data 
# Note:In page_detail.. If the keyword link "Unregistered Contractors" than do not pass the contractor name in bidder name field . only pass when it comes under "Contractor"

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_sa_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()

    notice_data.script_name = 'au_sa_ca'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'AUD'

    notice_data.main_language = 'EN'

    notice_data.procurement_method = 2

    notice_data.notice_type = 7
    
    # Onsite Field -Reference #
    # Onsite Comment -None

    try:
        notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Contract Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Start Date
    # Onsite Comment -None
    
    # Onsite Field -Total Cost
    # Onsite Comment -None
    
    try:
        deadline_date1 = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        if 'Sept' in deadline_date1:
            deadline_date =  deadline_date1.replace('Sept', 'Sep')
        else:
            deadline_date = deadline_date1
        tender_contract_end_date = re.findall('\d+ \w+ \d{4}',deadline_date)[0]
        try:
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        except:
            notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.tender_contract_end_date)
    except Exception as e:
        logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
        pass

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text.split('$ ')[1]
        notice_data.est_amount = float(est_amount.replace(',',''))
        notice_data.netbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    
    
    # Onsite Field -Contract Title
    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) a').get_attribute("href")
    except:
        pass
    try:
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    #     # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
        try:
            notice_data.notice_text += page_details.find_element(By.ID, '#content').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    #     # Onsite Field -UNSPSC
    #     # Ref_url=https://www.tenders.sa.gov.au/contract/view?id=201738

        try:
            notice_data.category = page_details.find_element(By.XPATH, '//*[contains(text(),"UNSPSC")]//following::div[1]').text
            cpv_codes = fn.CPV_mapping("assets/au_sa_ca_unspscpv.csv",notice_data.category)
            for cpv_code in cpv_codes:
                cpvs_data = cpvs()
                cpvs_data.cpv_code = cpv_code
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in category: {}".format(type(e).__name__))
            pass

    #     # Onsite Field -Procurement Process
        try:
            notice_data.document_type_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Procurement Process")]//following::div[1]').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

        try:
            publish_date = page_details.find_element(By.CSS_SELECTOR, "#content > div:nth-child(8) > div > div > span:nth-child(1)").text
            if 'Sept' in publish_date:
                publish_date =  publish_date.replace('Sept', 'Sep')
            else:
                publish_date = publish_date
            publish_date = re.findall('\d+ \w+ \d+, \d+:\d+ \w+',publish_date)[0]
            try:
                notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y, %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
            logging.info(notice_data.publish_date)
        except:
            try:
                publish_date = page_details.find_element(By.CSS_SELECTOR, "#content > div:nth-child(11) > div > div > span:nth-child(1)").text
                if 'Sept' in publish_date:
                    publish_date =  publish_date.replace('Sept', 'Sep')
                else:
                    publish_date = publish_date
                publish_date = re.findall('\d+ \w+ \d+, \d+:\d+ \w+',publish_date)[0]
                try:
                    notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    notice_data.publish_date = datetime.strptime(publish_date,'%d %b %Y, %H:%M %p').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return

        try:
            tender_contract_start_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Starting Date")]//following::div[1]').text
            tender_contract_start_date = re.findall('\d+ \w+ \d+',tender_contract_start_date)[0]
            try:
                notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in contract_start_date: {}".format(type(e).__name__))
            pass

        try:
            tender_contract_end_date = page_details.find_element(By.XPATH, '//*[contains(text(),"Completion Date")]//following::div[1]').text
            tender_contract_end_date = re.findall('\d+ \w+ \d+',tender_contract_end_date)[0]
            try:
                notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %b %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
        except Exception as e:
            logging.info("Exception in tender_contract_end_date: {}".format(type(e).__name__))
            pass

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Good or Services Acquired")]//following::div[1]').text
            notice_data.notice_summary_english = notice_data.local_description
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

    # # Ref_url=https://www.tenders.sa.gov.au/contract/view?id=205915

        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content'):
                customer_details_data = customer_details()
            # Onsite Field -Public Authority
                customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Public Authority")]//following::div[1]').text


            # Onsite Field -Freedom of Information Officer
            # Onsite Comment -Note:take a first line........Ex,"DHS FOI Officer (Freedom of Information) DHSFreedomofInformation@sa.gov.au Office: +61 (08) 84139050" Take only "DHS FOI Officer (Freedom of Information)"

                try:
                    customer_details_data.contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Freedom of Information Officer")]//following::div[1]').text.split('\n')[0]
                except Exception as e:
                    logging.info("Exception in contact_person: {}".format(type(e).__name__))
                    pass

            # Onsite Field -None
            # Onsite Comment -None

                try:
                    customer_details_data.org_email = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr > td:nth-child(2) > a').text
                except Exception as e:
                    logging.info("Exception in org_email: {}".format(type(e).__name__))
                    pass

            # Onsite Field -Freedom of Information Officer
            # Onsite Comment -Note:Splite after "Office","Phone:" this keyword

                try:
                    customer_details_data.org_phone = page_details.find_element(By.CSS_SELECTOR, 'tbody > tr:nth-child(2) > td:nth-child(2)').text
                except Exception as e:
                    logging.info("Exception in org_phone: {}".format(type(e).__name__))
                    pass

                customer_details_data.org_country = 'AU'
                customer_details_data.org_language = 'EN'
                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

    # # Onsite Field -Contract Attachments
    # # Onsite Comment -None
    # # Ref_url=https://tenders.sa.gov.au/contract/view?id=209119

        try:              
            for single_record in page_details.find_elements(By.XPATH, '//*[contains(text(),"Contract Attachments")]//following::div[1]/a'):
                attachments_data = attachments()
            # Onsite Comment -Note:Don't take file extention

                attachments_data.file_name = single_record.text.split('.')[0]

            # Onsite Comment -Note:Take only file extention
                try:
                    attachments_data.file_type = single_record.text.split('.')[-1]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                external_url = single_record
                page_details.execute_script("arguments[0].click();",external_url)
                file_dwn = Doc_Download.file_download()
                attachments_data.external_url = str(file_dwn[0])

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)

        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

    # # Onsite Field -None
    # # Onsite Comment -None

        try:              
            lot_details_data = lot_details()
                # Onsite Field -Reference #
            lot_details_data.lot_number=1
            lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text

            # Onsite Comment -Note:If the keyword link "Unregistered Contractors" than do not pass the contractor name in bidder name field . only pass when it comes under "Contractor"
            # Ref_url=https://www.tenders.sa.gov.au/contract/view?id=208811
            try:
                for single_record in page_details.find_elements(By.CSS_SELECTOR, '#content > div:nth-child(7) table tbody tr '):
                    award_details_data = award_details()

                    award_details_data.bidder_name = single_record.find_element(By.CSS_SELECTOR, 'td.contractor-details > b').text

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
    except:
        pass
    
    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_type) +  str(notice_data.notice_url) 
    logging.info(notice_data.identifier)
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
    urls = ["https://www.tenders.sa.gov.au/contract/search?preset=organisationWide"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(2,10):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.XPATH,'/html/body/main/div/div/div[2]/table/tbody/tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[2]/table/tbody/tr')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/main/div/div/div[2]/table/tbody/tr')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'/html/body/main/div/div/div[2]/table/tbody/tr'),page_check))
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
