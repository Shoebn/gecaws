from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "au_epwqtenders_ca"
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


#Note:Open the site than click on "View Awarded Contracts >> QTender Awarded Contracts" this than grab the data

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "au_epwqtenders_ca"
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
    notice_data.script_name = 'au_epwqtenders_ca'
    
    # Onsite Field -None
    # Onsite Comment -None
    performance_country_data = performance_country()
    performance_country_data.performance_country = 'AU'
    notice_data.performance_country.append(performance_country_data)
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.currency = 'AUD'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.main_language = 'EN'
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.procurement_method = 2
    
    # Onsite Field -None
    # Onsite Comment -None
    notice_data.notice_type = 7
    
    # Onsite Field -Reference #
    # Onsite Comment -None

    try:
        notice_data.related_tender_id = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(1)').text
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass
    print(notice_data.related_tender_id)
    
    # Onsite Field -Title
    # Onsite Comment -None

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, ' tr > td:nth-child(2)').text
        notice_data.notice_title = notice_data.local_title
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass
    
    # Onsite Field -Value
    # Onsite Comment -None

    try:
        est_amount = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(4)').text.split('$')[1]
        if ',' in est_amount:
            notice_data.est_amount = est_amount.replace(',','')
        else:
            notice_data.est_amount = est_amount
        notice_data.est_amount = float(notice_data.est_amount)
        notice_data.grossbudgetlc = notice_data.est_amount
    except Exception as e:
        logging.info("Exception in est_amount: {}".format(type(e).__name__))
        pass
    

#     # Onsite Field -Award Date
#     # Onsite Comment -None

    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, " td:nth-child(3)").text
        publish_date = re.findall('\d{4}-\d+-\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%Y-%m-%d').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return    
    
#     # Onsite Field -Title
#     # Onsite Comment -None

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2) a').get_attribute("href")                     
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url
    
#     # Onsite Field -None
#     # Onsite Comment -Note:along with notice text (page detail) also take data from tender_html_element (main page) ---- give td / tbody of main pg
    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#content_content > table:nth-child(2) > tbody').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')
    
#     # Onsite Field -Title
#     # Onsite Comment -Note:Notice_no teke from url....Ex,.("https://qtenders.epw.qld.gov.au/qtenders/contract/view.do?CSRFNONCE=B91D0464377797E1A14918A5B3A69A95&id=39&returnUrl=%252Fcontract%252Flist.do%253FCSRFNONCE%253DB989EAC42D0A46E01644FCAC69F05B18%2526amp%253Baction%253DgotoPage%2526amp%253BsortBy%253D%2526amp%253BissuingBusinessIdForSort%253D%2526amp%253BisSearch%253Dtrue%2526amp%253BpageNum%253D1%2526amp%253Bkeywords%253D%2526amp%253BcontractTitle%253D%2526amp%253BissuingBusinessId%253D-1%2526amp%253Breference%253D%2526amp%253Bvalue%253D%2526amp%253BclosingDateFromString%253D%2526amp%253BclosingDateToString%253D%2526amp%253BawardDateFromString%253D%2526amp%253BawardDateToString%253D%2526amp%253BstartingDateFromString%253D%2526amp%253BstartingDateToString%253D%2526amp%253BregionId%253D-1%2526amp%253BunspscCode1%253D%2526amp%253BunspscCode2%253D%2526amp%253BunspscCode3%253D" take only "39")..........id=39

    try:
        notice_data.notice_no = notice_data.notice_url.split('id=')[1].split('&')[0]
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Type of Work
#     # Onsite Comment -Note:Repleace following keywords with given keywords("Goods and Services=Supply and Service","Works=Works")

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of Work")]//following::td[1]').text
        if 'Goods and Services' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        elif 'Works' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Works'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    

    try:
        notice_data.local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Description
#     # Onsite Comment -None

    try:
        notice_data.notice_summary_english = page_details.find_element(By.XPATH, '//*[contains(text(),"Description")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -UNSPSC
#     # Onsite Comment -None
    try:
        notice_data.category = page_details.find_element(By.XPATH, "//*[contains(text(),'UNSPSC 1')]//following::td[1]").text
        cpv_codes = fn.CPV_mapping("assets/au_epwqtenders_ca_unspscpv.csv",notice_data.category)
        for cpv_code in cpv_codes:
            cpvs_data = cpvs()
            cpvs_data.cpv_code = cpv_code
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in category: {}".format(type(e).__name__))
        pass
    
#     # Onsite Field -Period Contract
#     # Onsite Comment -None

    try:
        notice_data.contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Period Contract")]//following::td[1]').text
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass
    
# # Onsite Field -None
# # Onsite Comment -None
# # Ref_url=https://qtenders.epw.qld.gov.au/qtenders/contract/view.do?CSRFNONCE=F269706D70FE8D020E3F48B0D62012EC&id=26&returnUrl=%252Fcontract%252Flist.do%253Faction%253Dcontract-search-submit%2526amp%253BCSRFNONCE%253D30375BE6403DEC5423FF022EBE71761A%2526amp%253BsortBy%253D%2526amp%253BissuingBusinessIdForSort%253D%2526amp%253BisSearch%253Dtrue%2526amp%253BpageNum%253D1%2526amp%253Bkeywords%253D%2526amp%253BcontractTitle%253D%2526amp%253BissuingBusinessId%253D-1%2526amp%253Breference%253D%2526amp%253Bvalue%253D%2526amp%253BclosingDateFromString%253D%2526amp%253BclosingDateToString%253D%2526amp%253BawardDateFromString%253D%2526amp%253BawardDateToString%253D%2526amp%253BstartingDateFromString%253D%2526amp%253BstartingDateToString%253D%2526amp%253BregionId%253D-1%2526amp%253BunspscCode1%253D%2526amp%253BunspscCode2%253D%2526amp%253BunspscCode3%253D

    try:              
        customer_details_data = customer_details()
    #         # Onsite Field -Agency
    #         # Onsite Comment -None

        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Agency")]//following::td[1]').text


#         # Onsite Field -Address
#         # Onsite Comment -None

        try:
            customer_details_data.org_address = page_details.find_element(By.XPATH, '//*[contains(text(),"Address")]//following::td[1]|//*[contains(text(),"Agency Unit")]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Contact
    #         # Onsite Comment -None

        try:
            customer_details_data.contact_person = page_details.find_element(By.XPATH, '(//*[contains(text(),"Contact")])[3]//following::td[1]').text
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -Phone
    #         # Onsite Comment -Note:Splite after "PHONE  or  OFFICE " this keyword

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::td[1]').text
            if 'PHONE:' in customer_details_data.org_phone:
                customer_details_data.org_phone = customer_details_data.org_phone.split('PHONE:')[1].split('\n')[0]
            else:
                customer_details_data.org_phone = customer_details_data.org_phone.split(':')[1]
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

#         # Onsite Field -Phone
#         # Onsite Comment -Note:Splite after "FAX" this keyword

        try:
            org_fax = page_details.find_element(By.XPATH, '//*[contains(text(),"Phone")]//following::td[1]').text
            if 'FAX: ' in org_fax:
                customer_details_data.org_fax = org_fax.split('FAX:')[1].split('\n')[0]
            else:
                pass

        except Exception as e:
            logging.info("Exception in org_fax: {}".format(type(e).__name__))
            pass

    #         # Onsite Field -E-Mail
    #         # Onsite Comment -None

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//*[contains(text(),"E-Mail")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass
        customer_details_data.org_country = 'AU'
        customer_details_data.org_language = 'EN'        
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass
    
# # Onsite Field -None
# # Onsite Comment -None

    try:              
        lot_details_data = lot_details()
    #         # Onsite Field -Title
    #         # Onsite Comment -None
        lot_details_data.lot_number = 1
        lot_details_data.lot_title = tender_html_element.find_element(By.CSS_SELECTOR, 'tr > td:nth-child(2)').text

        
#         # Onsite Field -Contractors
#         # Onsite Comment -None
#         # Ref_url=https://qtenders.epw.qld.gov.au/qtenders/contract/view.do?CSRFNONCE=97DD990EADB2AAF3505DEFACFA4F4A09&id=39585&returnUrl=%252Fcontract%252Flist.do%253FCSRFNONCE%253D8369913E7BD72FB33F9D9D706EEA8653%2526amp%253Baction%253DgotoPage%2526amp%253BsortBy%253D%2526amp%253BissuingBusinessIdForSort%253D%2526amp%253BisSearch%253Dtrue%2526amp%253BpageNum%253D984%2526amp%253Bkeywords%253D%2526amp%253BcontractTitle%253D%2526amp%253BissuingBusinessId%253D-1%2526amp%253Breference%253D%2526amp%253Bvalue%253D%2526amp%253BclosingDateFromString%253D%2526amp%253BclosingDateToString%253D%2526amp%253BawardDateFromString%253D%2526amp%253BawardDateToString%253D%2526amp%253BstartingDateFromString%253D%2526amp%253BstartingDateToString%253D%2526amp%253BregionId%253D-1%2526amp%253BunspscCode1%253D%2526amp%253BunspscCode2%253D%2526amp%253BunspscCode3%253D

        try:
            award_text = page_details.find_element(By.XPATH, '//*[contains(text(),"Contractors")]//following::table[1]').text
            award_text_1 =award_text.split(')')

            for i in award_text_1[1:]:
                award_details_data = award_details()
                award_details_data.bidder_name = i.split('\n')[0].strip()

                try:
                    award_details_data.address = i.split('\n')[1].split('\n')[0].strip()
                except:
                    pass

                try:
                    award_details_data.grossawardvaluelc = float(i.split('Price: $')[1].split('\n')[0].strip())
                except:
                    pass
                try:
                    award_date = publish_date
                    award_details_data.award_date = datetime.strptime(award_date,'%Y-%m-%d').strftime('%Y/%m/%d')
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
    th = date.today() - timedelta(70)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ["https://qtenders.epw.qld.gov.au/qtenders/contract/list.do?CSRFNONCE=5C9329CEF68125CA8A65838D4E5C9623&action=contract-search-submit&sortBy=&issuingBusinessIdForSort=&isSearch=true&pageNum=1&keywords=&contractTitle=&issuingBusinessId=-1&reference=&value=&closingDateFromString=&closingDateToString=&awardDateFromString=01%2F11%2F2023&awardDateToString=01%2F01%2F2024&startingDateFromString=&startingDateToString=&regionId=-1&unspscCode1=&unspscCode2=&unspscCode3="] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        try:
            for page_no in range(2,5):
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#sortableTable > tbody'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#sortableTable > tbody')))
                length = len(rows)
                for records in range(0,length):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#sortableTable > tbody')))[records]
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
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.XPATH,'//*[@id="sortableTable"]//following::tr[not(@style="display:none")]'),page_check))
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
