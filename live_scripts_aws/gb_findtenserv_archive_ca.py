from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "gb_findtenserv_archive_ca"
log_config.log(SCRIPT_NAME)
import re
import time
import jsons
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn
from selenium.webdriver.chrome.options import Options

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
tnotice_count = 0
SCRIPT_NAME = "gb_findtenserv_archive_ca"
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    global tnotice_count
    notice_data = tender()
    
    notice_data.script_name = 'gb_findtenserv_archive_ca'
    notice_data.main_language = 'EN'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'GB'
    notice_data.performance_country.append(performance_country_data)

    notice_data.currency = 'GBP'
    notice_data.procurement_method = 2
    notice_data.notice_type = 7
    notice_data.class_at_source = "CPV"
    
    try:
        notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div:nth-child(1) > dd').text
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass

    try:
        local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div > div.search-result-header').text            
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass     

    try:
        notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'div.search-result-header > h2 > a').get_attribute("href")
        fn.load_page(page_details,notice_data.notice_url,80)
        logging.info(notice_data.notice_url)
    except Exception as e:
        logging.info("Exception in notice_url: {}".format(type(e).__name__))
        notice_data.notice_url = url

    WebDriverWait(page_details, 100).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.govuk-width-container > main'))).text
    notice_text = page_details.find_element(By.CSS_SELECTOR, 'div.govuk-width-container > main').text
    
    try:
        tender_contract_start_date1 = notice_text.split("VII.1.5) Duration of the contract, framework agreement, dynamic purchasing system or concession")[1]
        tender_contract_start_date = tender_contract_start_date1.split('Start date')[1].split("\n")[1]
        tender_contract_start_date = re.findall('\d+ \w+ \d{4}',tender_contract_start_date)[0]
        notice_data.tender_contract_start_date = datetime.strptime(tender_contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    try:
        tender_contract_end_date1 = tender_contract_start_date1
        tender_contract_end_date = tender_contract_end_date1.split('End date')[1].split("\n")[1]
        tender_contract_end_date = re.findall('\d+ \w+ \d{4}',tender_contract_end_date)[0]
        notice_data.tender_contract_end_date = datetime.strptime(tender_contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
    except:
        pass
    
    try:
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text 
        notice_data.cpv_at_source = cpv_code.split('-')[0].strip()
    except Exception as e:
        logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
        pass

    try:
        cpvs_data = cpvs()
        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text 
        cpvs_data.cpv_code = cpv_code.split('-')[0].strip()
        cpvs_data.cpvs_cleanup()
        notice_data.cpvs.append(cpvs_data)
    except Exception as e:
        logging.info("Exception in cpv_code: {}".format(type(e).__name__))
        pass 
    
    try:
        local_description1 = notice_text.split("II.1.4) Short description")[1].split("II.1.6) Information about lots")[0].replace('\n','').replace('\n','')
        lot1 = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.6) Information about lots")]//following::p[1]').text
        if 'No' in lot1:
            try:
                local_description2 = fn.get_string_between(notice_text,'Description of the procurement','II.2.5) Award criteria')
                notice_data.local_description = local_description1+' '+local_description2
            except:
                try:
                    local_description2 = fn.get_string_between(notice_text,'Description of the procurement','II.2.11) Information about options')
                    notice_data.local_description = local_description1+' '+local_description2
                except:
                    notice_data.local_description = local_description1
        else:
            notice_data.local_description = local_description1
    except Exception as e:
        logging.info("Exception in local_description: {}".format(type(e).__name__))
        pass
    
    if 'N/A' in local_title:
        notice_data.local_title = local_description1
    else:
        notice_data.local_title = local_title
    notice_data.notice_title = notice_data.local_title
    
    try:         
        notice_data.notice_summary_english = notice_data.local_description
    except Exception as e:
        logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
        pass
     
    try:
        publish_date = page_details.find_element(By.CSS_SELECTOR, "div.govuk-grid-column-three-quarters> p:nth-child(4)").text 
        publish_date = re.findall('\d+ \w+ \d{4}, \d+:\d+[apAP][mM]', publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d %B %Y, %I:%M%p').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass
        
    try:
        lots_No = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.6) Information about lots")]//following::p[1]').text
        if 'No' in lots_No:
            notice_data.is_lot_default = True
    except Exception as e:
        logging.info("Exception in is_lot_default: {}".format(type(e).__name__))
        pass 

    try: 
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, 'div.govuk-width-container > main').get_attribute("outerHTML")                     
    except Exception as e:
        logging.info("Exception in notice_text: {}".format(type(e).__name__))
        pass
    
    try:
        lot1 = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.6) Information about lots")]//following::p[1]').text
        if 'No' in lot1:
            try:
                netbudgetlc1 = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.7) Total value of the procurement (excluding VAT)")]//following::p[1]').text
                if '£' in netbudgetlc1 and 'Highest offer:' in netbudgetlc1:
                    netbudgetlc = netbudgetlc1.split('Highest offer:')[1]
                    netbudgetlc =  re.sub("[^\d\.]", "",netbudgetlc)
                    notice_data.netbudgetlc = float(netbudgetlc.strip())
                    notice_data.est_amount = notice_data.netbudgetlc
                elif '£' in netbudgetlc1:
                    netbudgetlc = netbudgetlc1.split('£')[1]
                    netbudgetlc =  re.sub("[^\d\.]", "",netbudgetlc)
                    notice_data.netbudgetlc = float(netbudgetlc.strip())
                    notice_data.est_amount = notice_data.netbudgetlc
            except:
                try:
                    grossbudgeteuro1 = page_details.find_element(By.XPATH, '//*[contains(text(),"II.1.7) Total value of the procurement (excluding VAT)")]//following::p[1]').text
                    if '€' in grossbudgeteuro1:
                        grossbudgeteuro =  re.sub("[^\d\.]", "",grossbudgeteuro1)
                        notice_data.grossbudgeteuro = float(grossbudgeteuro.strip())
                        notice_data.netbudgeteuro = notice_data.grossbudgeteuro
                except:
                    pass 
    except:
        pass
    
    try:
        lot_number = 1
        page_details.find_element(By.XPATH, '//*[contains(text(),"II.2.1) Title")]//following::p[1]')
        lot_text = notice_text.split("II.2.1) Title")
        for lot in lot_text[1:]:
            lot_details_data = lot_details()
            lot_details_data.lot_number = lot_number
            
            try:
                lot_details_data.lot_actual_number = fn.get_string_between(lot,'Lot No','II.2.2) Additional CPV code(s)')
            except:
                lot_details_data.lot_actual_number = lot.split('-')[0].strip()
                
            try:
                contract_start_date1 = notice_text.split("II.2.7) Duration of the contract, framework agreement, dynamic purchasing system or concession")[1]
                contract_start_date = contract_start_date1.split('Start date')[1].split("\n")[1]
                contract_start_date = re.findall('\d+ \w+ \d{4}',contract_start_date)[0]
                lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
    
            try:
                contract_end_date1 = contract_start_date1
                contract_end_date = contract_end_date1.split('End date')[1].split("\n")[1]
                contract_end_date = re.findall('\d+ \w+ \d{4}',contract_end_date)[0]
                lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
            except:
                pass
      
            try:
                try:
                    lot_details_data.lot_description = fn.get_string_between(lot,'Description of the procurement','II.2.5) Award criteria')
                except:
                    lot_details_data.lot_description = fn.get_string_between(lot,'Description of the procurement','II.2.11) Information about options')
            except Exception as e:
                lot_details_data.lot_description = notice_data.local_description
                logging.info("Exception in lot_description: {}".format(type(e).__name__))
                pass
            
            lot_details_data.lot_title = lot.split("\n")[1]
            if lot_details_data.lot_title =='' or 'Lot No' in lot_details_data.lot_title:
                lot_details_data.lot_title = lot_details_data.lot_description 
                
            try:
                lot_details_data.lot_nuts = fn.get_string_between(lot,'NUTS codes','Main site or place of performance')
                
            except:
                try:
                    lot_details_data.lot_nuts = fn.get_string_between(lot,'NUTS codes','II.2.4) Description of the procurement')
                except Exception as e:
                    logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                    pass
            
            try:
                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p[1]').text
                if 'Services' in lot_details_data.lot_contract_type_actual :
                     lot_details_data.contract_type = 'Service'
                elif 'Works' in lot_details_data.lot_contract_type_actual :
                     lot_details_data.contract_type = 'Works'
                elif 'Supplies' in lot_details_data.lot_contract_type_actual :
                    lot_details_data.contract_type = 'Supply'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                pass

            try: 
                contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"VII.1.5) Duration of the contract, framework agreement, dynamic purchasing system or concession")]//following::p[1]').text
                duration = page_details.find_element(By.XPATH, '//*[contains(text(),"VII.1.5) Duration of the contract, framework agreement, dynamic purchasing system or concession")]//following::h5[1]').text
                if 'Duration in months' in duration :
                    contract_duration = re.findall("\d+",contract_duration)[1]
                    lot_details_data.contract_duration = "Duration in months "+ contract_duration
            except Exception as e:
                logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                pass
            
            try:
                if 'Additional CPV code(s)' in lot:
                    lot_cpv_cod = fn.get_string_between(lot,'Additional CPV code(s)','II.2.3) Place of performance')
                    lot_c = lot_cpv_cod.split("\n")
                    for lot in lot_c[1:]:
                        lot_cpvs_data = lot_cpvs()
                        cpv_regex = re.compile(r'\d{8}')
                        lot_cpvs_dataa = cpv_regex.findall(lot)[0]
                        lot_cpvs_data.lot_cpv_code = lot_cpvs_dataa
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                else:
                    lot_cpvs_data = lot_cpvs()
                    lot_cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text 
                    lot_cpvs_data.lot_cpv_code = lot_cpv_code.split('-')[0].strip()
                    lot_cpvs_data.lot_cpvs_cleanup()
                    lot_details_data.lot_cpvs.append(lot_cpvs_data)
            except Exception as e:
                    logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                    pass   
                
            try:
                single_record = fn.get_string_between(lot,'Additional CPV code(s)','II.2.3) Place of performance')
                cpv_regex = re.compile(r'\d{8}')
                cpv_at_sources = cpv_regex.findall(single_record)
                cpv_at_source = ''
                for cpv1 in cpv_at_sources:
                    cpv_at_source += cpv1  
                    cpv_at_source += ',' 
                cpv_source = cpv_at_source.rstrip(',')
                lot_details_data.lot_cpv_at_source = cpv_source
                notice_data.cpv_at_source += ',' + lot_details_data.lot_cpv_at_source
            except:
                try:
                    single_record = page_details.find_element(By.XPATH, '//*[contains(text(),"Main CPV code")]//following::ul[1]').text 
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

            try:
                award_date1 = re.search(r'V\.2\.1\) Date of conclusion of the contract\n(.+)', notice_text).group()
                award_date = re.findall('\d+ \w+ \d{4}',award_date1)[0]
                lot_details_data.lot_award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
            except:
                try:  
                    award_date1 = re.search(r'V\.2\.1\) Date of conclusion of the contract\/concession award decision\n(.+)', notice_text).group()
                    award_date = re.findall('\d+ \w+ \d{4}',award_date1)[0]
                    lot_details_data.lot_award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
                except:
                    pass
                
            try:
                tender_c = notice_text.split('2.5) Award criteria\n')[1].split("II.2.11) Information about options")[0].strip()
                tender_c_list = tender_c.split('\n')
                for LOT in tender_c_list:
                    if 'Quality criterion' in LOT or 'Price' in LOT or 'Cost criterion' in LOT:
                        lot_criteria_data = lot_criteria()
                        lot_criteria_data.lot_criteria_title = LOT.split("/")[0].strip()

                        try:
                            lot_criteria_data.lot_criteria_weight = int(LOT.split("Weighting:")[1].split("%")[0].strip())
                        except:
                            try:
                                lot_criteria_data.lot_criteria_weight = int(LOT.split("Weighting:")[1].split("%")[0].split('.')[0].strip())
                            except:
                                lot_criteria_data.lot_criteria_weight = int(LOT.split("Weighting:")[1].strip())
                        if 'Price' in lot_criteria_data.lot_criteria_title :
                            lot_criteria_data.lot_criteria_title = "Price"
                        if 'Price' in lot_criteria_data.lot_criteria_title or 'Cost' in lot_criteria_data.lot_criteria_title:
                            lot_criteria_data.lot_is_price_related = True
                        lot_criteria_data.lot_criteria_cleanup()
                        lot_details_data.lot_criteria.append(lot_criteria_data)  
            except Exception as e:
                logging.info("Exception in lot_criteria_data: {}".format(type(e).__name__))
                pass    

            try:
                try:
                    bidder_n = page_details.find_element(By.XPATH, '//*[contains(text(),"Section V. Award of contract")]')
                except:
                    bidder_n = page_details.find_element(By.XPATH, '//*[contains(text(),"Section V. Award of contract/concession")]')
                    
                try:
                    bidder_name1 = notice_text.split('Section V. Award of contract')
                except:
                    bidder_name1 = notice_text.split('Section V. Award of contract/concession')
                    
                for bidder_name2 in bidder_name1[1:]:
                    bidder_name = re.findall(r'Name and address of the contractor\/concessionaire\n(.+)', bidder_name2)
                    if bidder_name == []:
                        bidder_name = re.findall(r'V\.2\.3\) Name and address of the contractor\n(.+)', bidder_name2)

                    try:
                        award_date1 = re.search(r'V\.2\.1\) Date of conclusion of the contract\n(.+)', bidder_name2).group()
                    except:
                        pass
                    
                    try:
                        netawardvaluelc1 = re.search(r'Total value of the contract\/lot:(.+)', bidder_name2).group()
                    except:
                        try:
                            netawardvaluelc1 = re.search(r'Information on value of contract\/lot \(excluding VAT\)\n(.+)', bidder_name2).group()
                        except:
                            pass

                    try:
                        initial_estimated_value1 = re.search(r'Initial estimated total value of the contract\/lot:(.+)', bidder_name2).group()
                    except:
                        pass

                    for bidder in bidder_name:
                        award_details_data = award_details()
                        award_details_data.bidder_name = bidder
                        
                        try:
                            award_details_data.address = bidder_name2.split(bidder)[1].split("Country")[0]
                        except Exception as e:
                            logging.info("Exception in address: {}".format(type(e).__name__))
                            pass

                        try:
                            initial_estimated_value = initial_estimated_value1
                            initial_estimated_value =  re.sub("[^\d\.]", "",initial_estimated_value)
                            award_details_data.initial_estimated_value = float(initial_estimated_value.strip())            
                        except:
                            pass

                        try:
                            award_date = re.findall('\d+ \w+ \d{4}',award_date1)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
                        except:
                            pass

                        try:
                            try:
                                netawardvaluelc = netawardvaluelc1
                                if '£' in netawardvaluelc:
                                    netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                    netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                    award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                            except:
                                try:
                                    netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of contract/lot/concession (excluding VAT)")]//following::p[1]').text
                                    if '£' in netawardvaluelc:
                                        netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                        netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                        award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                                except:
                                    try:
                                        netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of the contract/lot/concession (at the time of conclusion of the contract;excluding VAT)")]//following::p[1]').text
                                        if '£' in netawardvaluelc:
                                            netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                            netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                            award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                                    except:
                                        try:
                                            netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of contract/lot (excluding VAT)")]//following::p[2]').text
                                            if '£' in netawardvaluelc:
                                                netawardvaluelc = netawardvaluelc.split('Highest offer:')[1].strip()
                                                netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                                award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                                        except:
                                            netawardvaluelc = netawardvaluelc1
                                            if '£' in netawardvaluelc:
                                                netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                                netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                                award_details_data.netawardvaluelc = float(netawardvaluelc.strip())

                        except:
                            try:
                                netawardvalueeuro = netawardvaluelc1
                                if '€' in netawardvalueeuro:
                                    netawardvalueeuro = netawardvalueeuro.split('£')[1].strip()
                                    netawardvalueeuro =  re.sub("[^\d\.]", "",netawardvalueeuro)
                                    award_details_data.netawardvalueeuro = float(netawardvalueeuro.strip())
                            except Exception as e:
                                pass
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
            except:
                try:
                    award_details_data = award_details()
                    award_details_data.bidder_name = page_details.find_element(By.XPATH,'//*[contains(text(),"Name and address of the contractor")]//following::p[1]').text
                    try:
                        award_date1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of conclusion of the contract")]//following::p[1]').text
                        award_date = re.findall('\d+ \w+ \d{4}',award_date1)[0]
                        award_details_data.award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
                    except:
                        pass
                    try:
                        address_1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[1]').text 
                        address_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[2]').text 
                        address_3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[3]').text  
                        address_4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[4]').text 
                        award_details_data.address = f"{address_1} {address_2} {address_3} {address_4}"
                    except Exception as e:
                        logging.info("Exception in address: {}".format(type(e).__name__))
                        pass

                    try:
                        initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Initial estimated total value of the contract/lot:")]').text 
                        initial_estimated_value = initial_estimated_value.split('£')[1].strip()
                        initial_estimated_value =  re.sub("[^\d\.]", "",initial_estimated_value)
                        award_details_data.initial_estimated_value = float(initial_estimated_value.strip())            
                    except:
                        pass
                    
                    try:
                        try:
                            netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"Total value of the contract/lot:")]').text
                            if '£' in netawardvaluelc:
                                netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                        except:
                            try:
                                netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of contract/lot/concession (excluding VAT)")]//following::p[1]').text
                                if '£' in netawardvaluelc:
                                    netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                    netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                    award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                            except:
                                try:
                                    netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of the contract/lot/concession (at the time of conclusion of the contract;excluding VAT)")]//following::p[1]').text
                                    if '£' in netawardvaluelc:
                                        netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                        netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                        award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                                except:
                                    netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of contract/lot (excluding VAT)")]//following::p[2]').text
                                    if '£' in netawardvaluelc:
                                        netawardvaluelc = netawardvaluelc.split('Highest offer:')[1].strip()
                                        netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                        award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                    except:
                        try:
                            netawardvalueeuro = page_details.find_element(By.XPATH,'//*[contains(text(),"Total value of the contract/lot:")]').text
                            if '€' in netawardvalueeuro:
                                netawardvalueeuro = netawardvalueeuro.split('£')[1].strip()
                                netawardvalueeuro =  re.sub("[^\d\.]", "",netawardvalueeuro)
                                award_details_data.netawardvalueeuro = float(netawardvalueeuro.strip())
                        except Exception as e:
                            pass
                    award_details_data.award_details_cleanup()
                    lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in lot_details_data: {}".format(type(e).__name__))
                    pass
        
            lot_details_data.lot_details_cleanup()
            notice_data.lot_details.append(lot_details_data)
            lot_number+=1
    except:
        try:
            lot_deatils = page_details.find_element(By.CSS_SELECTOR, 'div#main-content').text.split('II.2) Description')
            lot_number = 1
            for lot in lot_deatils[1:]:
                lot_details_data = lot_details()
                lot_details_data.lot_number = lot_number
                try:
                    lot_title = lot.split("Title")[1].split('\n')[1].split('\n')[0]
                    lot_details_data.lot_title = str(lot_title)   
                except:
                    lot_details_data.lot_title = notice_data.notice_title
                    notice_data.is_lot_default = True
                    
                try:
                    lot_details_data.lot_description = fn.get_string_between(notice_text,'Description of the procurement','II.2.5) Award criteria')
                except:
                    try:
                        lot_details_data.lot_description = fn.get_string_between(notice_text,'Description of the procurement','II.2.11) Information about options')
                    except Exception as e:
                        lot_details_data.lot_description = notice_data.local_description
                        logging.info("Exception in lot_description: {}".format(type(e).__name__))
                        pass
                
                try:
                    lot_details_data.contract_number = page_details.find_element(By.XPATH, '//*[contains(text(),"Contract No")]//following::p[1]').text
                except Exception as e:
                    logging.info("Exception in contract_number: {}".format(type(e).__name__))
                    pass
                
                try:
                    contract_start_date1 = notice_text.split("II.2.7) Duration of the contract, framework agreement, dynamic purchasing system or concession")[1]
                    contract_start_date = contract_start_date1.split('Start date')[1].split("\n")[1]
                    contract_start_date = re.findall('\d+ \w+ \d{4}',contract_start_date)[0]
                    lot_details_data.contract_start_date = datetime.strptime(contract_start_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    pass

                try:
                    contract_end_date1 = contract_start_date1
                    contract_end_date = contract_end_date1.split('End date')[1].split("\n")[1]
                    contract_end_date = re.findall('\d+ \w+ \d{4}',contract_end_date)[0]
                    lot_details_data.contract_end_date = datetime.strptime(contract_end_date,'%d %B %Y').strftime('%Y/%m/%d %H:%M:%S')
                except:
                    pass
      
                try:
                    lot_details_data.lot_nuts = lot.split('NUTS codes\n')[1].split('\n')[0] 
                except:
                    try:
                        lot_details_data.lot_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code")]//following::p[1]').text 
                    except Exception as e:
                        logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                        pass

                try:
                    lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p[1]').text
                    if 'Services' in lot_details_data.lot_contract_type_actual :
                         lot_details_data.contract_type = 'Service'
                    elif 'Works' in lot_details_data.lot_contract_type_actual :
                         lot_details_data.contract_type = 'Works'
                    elif 'Supplies' in lot_details_data.lot_contract_type_actual :
                        lot_details_data.contract_type = 'Supply'
                    else:
                        pass
                except Exception as e:
                    logging.info("Exception in contract_type: {}".format(type(e).__name__))
                    pass

                try:
                    contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"VII.1.5) Duration of the contract, framework agreement, dynamic purchasing system or concession")]//following::p[1]').text
                    duration = page_details.find_element(By.XPATH, '//*[contains(text(),"VII.1.5) Duration of the contract, framework agreement, dynamic purchasing system or concession")]//following::h5[1]').text
                    if 'Duration in months' in duration :
                        contract_duration = re.findall("\d+",contract_duration)[1]
                        lot_details_data.contract_duration = "Duration in months "+ contract_duration
                except Exception as e:
                    logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                    pass
                
                try:
                    award_date1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of conclusion of the contract")]//following::p[1]').text
                    award_date = re.findall('\d+ \w+ \d{4}',award_date1)[0]
                    lot_details_data.lot_award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
                except:
                    pass

                try:
                    lot_cpv_cod = notice_text.split("II.2.2) Additional CPV code(s)")[1].split("II.2.3) Place of performance")[0]
                    lot_c = lot_cpv_cod.split("\n")
                    for lot in lot_c[1:]:
                        lot_cpvs_data = lot_cpvs()
                        cpv_regex = re.compile(r'\d{8}')
                        lot_cpvs_dataa = cpv_regex.findall(lot)[0]
                        lot_cpvs_data.lot_cpv_code = lot_cpvs_dataa
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                except:
                    try:
                        lot_cpvs_data = lot_cpvs()
                        cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"VII.1.1) Main CPV code")]//following::ul[1]').text 
                        lot_cpvs_data.lot_cpv_code = cpv_code.split('-')[0].strip()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    except:
                        pass
                    
                try:
                    single_record = notice_text.split("II.2.2) Additional CPV code(s)")[1].split("II.2.3) Place of performance")[0]
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
                    
            
                try:
                    single_record = page_details.find_element(By.CSS_SELECTOR,'//*[contains(text(),"VII.1.1) Main CPV code")]//following::ul[1]').text
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
                    single_record = page_details.find_element(By.CSS_SELECTOR,'//*[contains(text(),"VII.1.1) Main CPV code")]//following::ul[1]').text
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
                    
                try:
                    tender_c = notice_text.split('2.5) Award criteria\n')[1].split("two.2.11)")[0].strip()
                    tender_c_list = tender_c.split('\n')
                    for LOT in tender_c_list:
                        if 'Quality criterion' in LOT or 'Price' in LOT or 'Cost criterion' in LOT:
                            lot_criteria_data = lot_criteria()
                            lot_criteria_data.lot_criteria_title = LOT.split("/")[0].strip()
                            try:
                                lot_criteria_data.lot_criteria_weight = int(LOT.split("Weighting:")[1].split("%")[0].strip())
                            except:
                                try:
                                    lot_criteria_data.lot_criteria_weight = int(LOT.split("Weighting:")[1].split("%")[0].split('.')[0].strip())
                                except:
                                    lot_criteria_data.lot_criteria_weight = int(LOT.split("Weighting:")[1].strip())

                            if 'Price' in lot_criteria_data.lot_criteria_title :
                                lot_criteria_data.lot_criteria_title  = "Price"
                            if 'Price' in lot_criteria_data.lot_criteria_title or 'Cost' in lot_criteria_data.lot_criteria_title:
                                lot_criteria_data.lot_is_price_related = True
                            lot_criteria_data.lot_criteria_cleanup()
                            lot_details_data.lot_criteria.append(lot_criteria_data)  
                except Exception as e:
                    logging.info("Exception in lot_criteria_data: {}".format(type(e).__name__))
                    pass    

                try:                    
                    bidder_name = re.findall(r'V\.2\.3\) Name and address of the contractor\n(.+)', notice_text)
                    if bidder_name == []:
                        bidder_name = re.findall(r'V\.2\.3\) Name and address of the contractor/concessionaire\n(.+)', notice_text)

                    for bidder in bidder_name:
                        award_details_data = award_details()
                        award_details_data.bidder_name = bidder
                        try:
                            award_date1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Date of conclusion of the contract")]//following::p[1]').text
                            award_date = re.findall('\d+ \w+ \d{4}',award_date1)[0]
                            award_details_data.award_date = datetime.strptime(award_date,'%d %B %Y').strftime('%Y/%m/%d')
                        except:
                            pass
                        
                        try:
                            address_1 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[1]').text 
                            address_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[2]').text 
                            address_3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[3]').text  
                            address_4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and address of the contractor")]//following::p[4]').text 
                            award_details_data.address = f"{address_1} {address_2} {address_3} {address_4}"
                        except Exception as e:
                            logging.info("Exception in address: {}".format(type(e).__name__))
                            pass

                        try:
                            initial_estimated_value = page_details.find_element(By.XPATH, '//*[contains(text(),"Initial estimated total value of the contract/lot:")]').text 
                            initial_estimated_value = initial_estimated_value.split('£')[1].strip()
                            initial_estimated_value =  re.sub("[^\d\.]", "",initial_estimated_value)
                            award_details_data.initial_estimated_value = float(initial_estimated_value.strip())            
                        except:
                            pass

                        try:
                            try:
                                netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"Total value of the contract/lot:")]').text
                                if '£' in netawardvaluelc:
                                    netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                    netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                    award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                            except:
                                try:
                                    netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of contract/lot/concession (excluding VAT)")]//following::p[1]').text
                                    if '£' in netawardvaluelc:
                                        netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                        netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                        award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                                except:
                                    try:
                                        netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of the contract/lot/concession (at the time of conclusion of the contract;excluding VAT)")]//following::p[1]').text
                                        if '£' in netawardvaluelc:
                                            netawardvaluelc = netawardvaluelc.split('£')[1].strip()
                                            netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                            award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                                    except:
                                        netawardvaluelc = page_details.find_element(By.XPATH,'//*[contains(text(),"V.2.4) Information on value of contract/lot (excluding VAT)")]//following::p[2]').text
                                        if '£' in netawardvaluelc:
                                            netawardvaluelc = netawardvaluelc.split('Highest offer:')[1].strip()
                                            netawardvaluelc =  re.sub("[^\d\.]", "",netawardvaluelc)
                                            award_details_data.netawardvaluelc = float(netawardvaluelc.strip())
                        except:
                            try:
                                netawardvalueeuro = page_details.find_element(By.XPATH,'//*[contains(text(),"Total value of the contract/lot:")]').text
                                if '€' in netawardvalueeuro:
                                    netawardvalueeuro = netawardvalueeuro.split('£')[1].strip()
                                    netawardvalueeuro =  re.sub("[^\d\.]", "",netawardvalueeuro)
                                    award_details_data.netawardvalueeuro = float(netawardvalueeuro.strip())
                            except Exception as e:
                                pass
                        award_details_data.award_details_cleanup()
                        lot_details_data.award_details.append(award_details_data)
                except Exception as e:
                    logging.info("Exception in lot_details_data: {}".format(type(e).__name__))
                    pass

                lot_details_data.lot_details_cleanup()
                notice_data.lot_details.append(lot_details_data)
                lot_number+=1
        except Exception as e:
            logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
            pass        

    try:
        notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice reference:")]').text
        notice_data.notice_no = notice_no.split('Notice reference:')[1].strip()
    except Exception as e:
        logging.info("Exception in notice_no: {}".format(type(e).__name__))
        pass
    
    try:
        notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[@id="main-content"]/div[5]/p[2]/a[1]').get_attribute("href")
        if notice_data.additional_tender_url =='' or 'http' not in notice_data.additional_tender_url:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address")]//following::a[1]').get_attribute("href")
    except:
        try:
            notice_data.additional_tender_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address")]//following::a[1]').get_attribute("href")
        except:
            pass

    try:
        notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Reference number")]//following::p[1]').text
    except:
        try:
            notice_data.related_tender_id = page_details.find_element(By.XPATH, '//*[contains(text(),"Notice number")]//following::a[1]').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass
    
    try:
        notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of procedure")]//following::p[1]').text  
        notice_data.type_of_procedure = fn.procedure_mapping("assets/uk_findtenserv_procedure.csv",notice_data.type_of_procedure_actual)
    except Exception as e:
        logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
        pass

    try:
        notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Type of contract")]//following::p').text
        if 'Services' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Service'
        elif 'Works' in notice_data.contract_type_actual:
             notice_data.notice_contract_type = 'Works'
        elif 'Supplies' in notice_data.contract_type_actual:
            notice_data.notice_contract_type = 'Supply'
        else:
            pass
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        netbudgetlc = page_details.find_element(By.XPATH,'//*[contains(text(),"Total value of the procurement (excluding VAT)")]//following::p[1]').text
        netbudgetlc = netbudgetlc.split('£')[1].strip()
        netbudgetlc = re.sub("[^\d\.]", "",netbudgetlc)
        notice_data.netbudgetlc = float(netbudgetlc)
    except Exception as e:
        logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
        pass
    
    try:
        contract_duration = page_details.find_element(By.XPATH, '//*[contains(text(),"Duration in months")]//following::p[1]').text
        contract_duration = re.findall("\d+",contract_duration)[1]
        notice_data.contract_duration = "Duration in months "+ contract_duration
    except Exception as e:
        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
        pass

    try:              
        customer_details_data = customer_details()
        customer_details_data.org_name = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[1]').text   
        try:
            customer_details_data.customer_main_activity = fn.get_string_between(notice_text,'Main activity','Section II: Object')
        except:
            pass
        
        try:
            customer_details_data.type_of_authority_code = notice_text.split("I.4) Type of the contracting authority")[1].split("I.5) Main activity")[0].strip()
        except:
            pass
        
        try:
            org_address_2 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[2]').text
            org_address_3 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[3]').text
            org_address_4 = page_details.find_element(By.XPATH, '//*[contains(text(),"Name and addresses")]//following::p[4]').text
            customer_details_data.org_address = f"{org_address_2} {org_address_3} {org_address_4}"
        except Exception as e:
            logging.info("Exception in org_address: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_email = page_details.find_element(By.XPATH, '//h4[text()="Email"]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in org_email: {}".format(type(e).__name__))
            pass

        try:
            contact_person = page_details.find_element(By.XPATH, '//*[contains(text(),"Contact")]//following::p[1]').text  
            if len(contact_person)<23:
                customer_details_data.contact_person = contact_person
        except Exception as e:
            logging.info("Exception in contact_person: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_phone = page_details.find_element(By.XPATH, '//*[contains(text(),"Telephone")]//following::p[1]').text 
        except Exception as e:
            logging.info("Exception in org_phone: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.customer_nuts = page_details.find_element(By.XPATH, '//*[contains(text(),"NUTS code")]//following::p[1]').text  
        except Exception as e:
            logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
            pass

        try:
            customer_details_data.org_website = page_details.find_element(By.XPATH, '//*[contains(text(),"Main address")]//following::p[1]').text                 
        except Exception as e:
            logging.info("Exception in org_website: {}".format(type(e).__name__))
            pass
      
        customer_details_data.org_country = 'GB'
        customer_details_data.org_language = 'EN'
        customer_details_data.customer_details_cleanup()
        notice_data.customer_details.append(customer_details_data)
    except Exception as e:
        logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
        pass       

    try:              
        attachments_data = attachments()
        attachments_data.external_url = page_details.find_element(By.XPATH, '//*[contains(text(),"Download")]//following::a[1]').get_attribute('href') 
        attachments_data.file_name = 'Download'
        if 'PDF' in attachments_data.external_url:
            attachments_data.file_type = 'PDF'
        attachments_data.attachments_cleanup()
        notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) +  str(notice_data.notice_url) +  str(notice_data.notice_type) + str(notice_data.publish_date) + str(notice_data.local_title)
    logging.info(notice_data.identifier)
    notice_data.tender_cleanup()
    output_json_file.writeNoticeToJSONFile(jsons.dump(notice_data))
    notice_count += 1
    tnotice_count += 1
    logging.info('----------------------------------')
# ----------------------------------------- Main Body
arguments= ['−−incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
options = Options()
for argument in arguments:
    options.add_argument(argument)
page_main = webdriver.Chrome( options=options)
page_details = webdriver.Chrome( options=options)

try:
    th = '01/01/2022'
    th1 = '28/12/2023'
    logging.info("Scraping from or greater than: " +th)
    urls = ["https://www.find-tender.service.gov.uk/Search/Results"] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        click_1 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="stage[4]_label"]')))
        page_main.execute_script("arguments[0].click();",click_1)           
        time.sleep(2)
        
        click_2 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="stage[1]_label"]')))
        page_main.execute_script("arguments[0].click();",click_2)      
        time.sleep(2)
        
        click_3 = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="stage[2]_label"]')))
        page_main.execute_script("arguments[0].click();",click_3) 
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
        
        for page_no in range(1,2000):# 2000
            url = 'https://www.find-tender.service.gov.uk/Search/Results?&page='+str(page_no)+'#dashboard_notices'
            fn.load_page(page_main, url, 50)
            logging.info(url)
            page_check = WebDriverWait(page_main, 100).until(EC.presence_of_element_located((By.XPATH,'//*[@id="dashboard_notices"]/div[1]/div'))).text
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
