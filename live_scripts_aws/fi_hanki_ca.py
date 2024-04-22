from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "fi_hanki_ca"
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
import gec_common.Doc_Download

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "fi_hanki_ca"
Doc_Download = gec_common.Doc_Download.Doc_Download(SCRIPT_NAME)
output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
previous_scraping_log_check = fn.previous_scraping_log_check(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    notice_data = tender()
    

#format 1  
#https://www.hankintailmoitukset.fi/fi/public/procurement/92953/notice/136810/overview

#format 2
#https://www.hankintailmoitukset.fi/fi/public/procedure/28/enotice/86/ 
    notice_data.script_name = 'fi_hanki_ca'


    notice_data.main_language = 'FI'
    

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'FI'
    notice_data.performance_country.append(performance_country_data)
    notice_data.currency = 'EUR'
    
    notice_data.notice_type = 7
    

    try:
        document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text 
    except Exception as e:
        logging.info("Exception in document_type_description: {}".format(type(e).__name__))
        pass
    
    notice_data.document_type_description = document_type_description
    
    if ' Kansallinen suorahankinta' in document_type_description or 'Kansalliset ilmoitukset' in document_type_description:

        notice_data.procurement_method = 0
    else:
        notice_data.procurement_method = 2

    try:
        notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
        notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
    except Exception as e:
        logging.info("Exception in local_title: {}".format(type(e).__name__))
        pass


    try:
        publish_date = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text
        publish_date = re.findall('\d+.\d+.\d{4} \d+:\d+',publish_date)[0]
        notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
        logging.info(notice_data.publish_date)
    except Exception as e:
        logging.info("Exception in publish_date: {}".format(type(e).__name__))
        pass

    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
        return

    try:
        notice_deadline = tender_html_element.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text
        notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+',notice_deadline)[0]
        notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M').strftime('%Y/%m/%d %H:%M:%S')
    except Exception as e:
        logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
        pass


    notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(2) > a').get_attribute("href")    
    fn.load_page(page_details,notice_data.notice_url,30)
    logging.info(notice_data.notice_url)


    try:
        Tarkemmat_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//a[contains(text(),"Tarkemmat tiedot")]'))).get_attribute("href")                     
        logging.info(Tarkemmat_url)
        fn.load_page(page_details1,Tarkemmat_url,100)
        time.sleep(3)
    except:
        pass

    try: 
        Ostajaorganisaatio_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//a[contains(text(),"Ostajaorganisaatio")]'))).get_attribute("href")                     
        logging.info(Ostajaorganisaatio_url)
        fn.load_page(page_details2,Ostajaorganisaatio_url,100)
        time.sleep(3)
    except:
        pass

    try:
        Osallistuminen_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//a[contains(text(),"Osallistuminen")]'))).get_attribute("href")                     
        logging.info(Osallistuminen_url)
        fn.load_page(page_details3,Osallistuminen_url,100)
        time.sleep(3)
    except:
        pass


    try:              
        for single_record in page_details.find_elements(By.CSS_SELECTOR, 'div:nth-child(3) > div > div > div:nth-child(8) > table > tbody >tr '):  

            attachments_data = attachments()

            file_name = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').text
            attachments_data.file_name = file_name

            try:
                file_type = file_name[-3:]
                attachments_data.file_type = file_type
            except Exception as e:
                logging.info("Exception in file_type: {}".format(type(e).__name__))
                pass

            external_url = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute('href')
            attachments_data.external_url = external_url

            attachments_data.attachments_cleanup()
            notice_data.attachments.append(attachments_data)
    except Exception as e:
        logging.info("Exception in attachments: {}".format(type(e).__name__)) 
        pass

    try:
        notice_data.related_tender_id = page_details1.find_element(By.XPATH, '(//*[contains(text(),"Edeltävän ilmoituksen TED-numero")])[2]//following::div[1]').text  
    except Exception as e:
        logging.info("Exception in related_tender_id: {}".format(type(e).__name__))
        pass

    try:
        notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
    except:
        notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

    try:
        notice_data.notice_no = page_details.find_element(By.XPATH, '//*[contains(text(),"Ilmoituksen Hilma-numero")]//following::span[1]').text  
    except Exception as e:
        notice_data.notice_no = notice_data.notice_url.split('notice/')[1].split('/')[0]

    if 'enotice' not in notice_data.notice_url: 
        logging.info('format 1')

        try:
            notice_data.local_description = page_details.find_element(By.XPATH, '(//*[contains(text(),"Lyhyt kuvaus")])[3]//following::div[1]').text 
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass
        notice_data.local_description = notice_data.local_description[:4000]
        notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '(//*[contains(text(),"Menettelyn luonne")])[3]//following::div[1]').text 
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fi_hanki_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass


        try:
            est_amount_1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Hankinnan yhteenlaskettu kokonaisarvo koko ajalle (ilman alv:ta)")])[2]//following::div[1]').text
        except:
            try:
                est_amount_1 = page_details.find_element(By.XPATH, '(//*[contains(text(),"Arvioitu kokonaisarvo")])[3]//following::div[3]').text
            except:
                pass

        try:        
            est_amount_2 = re.sub("[^\d\.\,]","",est_amount_1)
            notice_data.est_amount =float(est_amount_2.replace(' ','').strip())
            notice_data.netbudgeteuro = notice_data.est_amount
            notice_data.netbudgetlc = notice_data.est_amount
            notice_data.grossbudgetlc = notice_data.est_amount
            notice_data.netbudgetlc = notice_data.est_amount
        except Exception as e:
            logging.info("Exception in est_amount: {}".format(type(e).__name__))
            pass

        try:
            notice_contract_type = page_details.find_element(By.XPATH, '(//*[contains(text(),"Hankinnan tyyppi")])[2]//following::div[2]').text 
            notice_data.contract_type_actual =  notice_contract_type

            if "Urakat" in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            elif "Tavarat" in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            elif "Palvelut" in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            else:
                pass

        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass

        # Onsite Field -Hankintanimikkeistö 
        try:              

            cpvs_data = cpvs()
            cpv_code = page_details.find_element(By.XPATH, '(//*[contains(text(),"Hankintanimikkeistö")])[3]//following::div/div').text
            cpvs_data.cpv_code = re.findall('\d{8}',cpv_code)[0].strip()
            notice_data.class_at_source = 'CPV'
            notice_data.cpv_at_source = cpvs_data.cpv_code 
            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass


        try:
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, '#main > div > div.container > div > div > div > div > div:nth-child(3) > div > div'): 

                tender_text = single_record.text
                if 'Tarjousten vertailuperusteet' in tender_text:
                    tender_criteria_data = tender_criteria()


                    tender_criteria_data.tender_criteria_title = tender_text.split('Tarjousten vertailuperusteet')[1].split('\n')[1]  

                    tender_criteria_weight = int(tender_text.split('Hinta')[1].split('\n')[0].strip())
                    tender_criteria_data.tender_criteria_weight = int(tender_criteria_weight)

                    tender_criteria_data.tender_criteria_cleanup()
                    notice_data.tender_criteria.append(tender_criteria_data)
        except Exception as e:
            logging.info("Exception in tender_criteria: {}".format(type(e).__name__)) 
            pass


        try:
            lot_number = 1
            for single_record in page_details1.find_elements(By.CSS_SELECTOR, 'div.notice-public-lot'): 

                if 'Osan nimi' in single_record.text:   
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = lot_number

                    try:
                        lot_details_data.lot_actual_number = single_record.find_element(By.CSS_SELECTOR,'h2 > span').text.split('-')[0]
                    except Exception as e:
                        logging.info("Exception in lot_actual_number: {}".format(type(e).__name__))
                        pass

                    lot_details_data.contract_type = notice_data.notice_contract_type
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

                    lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'div>div:nth-child(2)').text 
                    lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title) 

                    try:
                        lot_details_data.lot_description = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(3)>div:nth-child(2)').text 
                        lot_details_data.lot_description = lot_details_data.lot_description[:4900]
                        lot_details_data.lot_description_english =   GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_description) 
                    except Exception as e:
                        logging.info("Exception in lot_description: {}".format(type(e).__name__))
                        pass 

                    try:
                        lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(7)>div:nth-child(2)').text  
                        lot_grossbudget_lc = lot_grossbudget_lc.split('EUR')[0].strip()
                        lot_grossbudget_lc = float(lot_grossbudget_lc.replace(' ','').strip())
                        lot_details_data.lot_grossbudget_lc = lot_grossbudget_lc
                    except Exception as e:
                        logging.info("Exception in lot_grossbudget_lc: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_details_data.lot_nuts = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(6)>div:nth-child(2)').text  
                    except Exception as e:
                        logging.info("Exception in lot_nuts: {}".format(type(e).__name__))
                        pass

                    try:
                        lot_details_data.contract_duration = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(9)>div:nth-child(2)>div>div>div>div').text 
                    except Exception as e:
                        logging.info("Exception in contract_duration: {}".format(type(e).__name__))
                        pass

                    try: 
                        lot_cpvs_data = lot_cpvs()
                        lot_cpv_code = single_record.find_element(By.CSS_SELECTOR, 'div:nth-child(5)>div:nth-child(2)').text 
                        lot_cpvs_data.lot_cpv_code = re.findall('\d{8}',lot_cpv_code)[0].strip()
                        lot_cpvs_data.lot_cpv_at_source = lot_cpvs_data.lot_cpv_code
                        lot_cpvs_data.lot_cpvs_cleanup()
                        lot_details_data.lot_cpvs.append(lot_cpvs_data)
                    except Exception as e:
                        logging.info("Exception in lot_cpvs: {}".format(type(e).__name__))
                        pass


                    try:
                        awd_num = lot_details_data.lot_number + 2
                        single_record = page_details.find_element(By.CSS_SELECTOR,'#main > div > div.container > div > div > div > div > div:nth-child(3) > div > div > div.notice-public-overview.card-body.preview > div:nth-child('+str(awd_num)+')')
                        if 'Virallinen nimi' in single_record.text:                 

                            for each_awardee in single_record.find_elements(By.CSS_SELECTOR,'div:nth-child(3) > div > div.awarded-contract.px-5'):

                                award_details_data = award_details()

                                award_details_data.bidder_name = each_awardee.find_element(By.CSS_SELECTOR,' div:nth-child(5) > div.mt-5 > div > div:nth-child(3) > div.value-row-value.col-12.col-sm-8').text

                                try:
                                    address = each_awardee.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > div.mt-5 > div > div:nth-child(4)').text.split('Postiosoite')[1].replace('\n','')
                                except:
                                    address = ''
                                    pass
                                try:
                                    zipcode = each_awardee.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.mt-5 > div > div:nth-child(5)').text.split('Postinumero')[1].replace('\n','')
                                except:
                                    zipcode = ''
                                    pass

                                try:
                                    district = each_awardee.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.mt-5 > div > div:nth-child(6)').text.split('Postitoimipaikka')[1].replace('\n','')
                                except:
                                    district = ''
                                    pass

                                try:
                                    country = each_awardee.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.mt-5 > div > div:nth-child(7)').text.split('Maa')[1].replace('\n','') 
                                except:
                                    country = ''
                                    pass

                                try:
                                    award_details_data.address = address +' '+zipcode+' '+district+' '+ country
                                except:
                                    pass

                                try:
                                    grossawardvaluelc = each_awardee.find_element(By.CSS_SELECTOR,'div:nth-child(4)').text
                                    grossawardvaluelc = grossawardvaluelc.replace('\n','')
                                    grossawardvaluelc = grossawardvaluelc.replace(' ','')
                                    pattern = '\d+EUR'
                                    grossawardvaluelc = re.findall(pattern,grossawardvaluelc)
                                    grossawardvaluelc = str(grossawardvaluelc)
                                    grossawardvaluelc = re.findall('\d+',grossawardvaluelc)[0]      
                                    award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                                    award_details_data.grossawardvalueeuro = award_details_data.grossawardvaluelc 
                                except Exception as e:
                                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                                    pass

                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)

                    except:
                        logging.info("Exception in award details: {}".format(type(e).__name__))
                        pass


                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number+=1
                else:
                    lot_details_data = lot_details()
                    lot_details_data.lot_number = 1

                    lot_details_data.contract_type = notice_data.notice_contract_type
                    lot_details_data.lot_contract_type_actual = notice_data.contract_type_actual

                    lot_details_data.lot_title = notice_data.local_title
                    notice_data.is_lot_default = True
                    lot_details_data.lot_title_english = notice_data.notice_title 


                    try:
                        awd_num = lot_details_data.lot_number + 2
                        single_record = page_details.find_element(By.CSS_SELECTOR,'#main > div > div.container > div > div > div > div > div:nth-child(3) > div > div > div.notice-public-overview.card-body.preview > div:nth-child('+str(awd_num)+')')
                        if 'Virallinen nimi' in single_record.text:                 

                            for each_awardee in single_record.find_elements(By.CSS_SELECTOR,'#main > div > div.container > div > div > div > div > div:nth-child(3) > div > div > div.notice-public-overview.card-body.preview > div:nth-child(3) > div:nth-child(2) > div > div.awarded-contract.px-5 > div:nth-child(5) > div.mt-5 >  div  '):

                                award_details_data = award_details()

                                award_details_data.bidder_name = each_awardee.find_element(By.CSS_SELECTOR,'  div > div:nth-child(3)').text.split('Virallinen nimi')[1]

                                try:
                                    address = each_awardee.find_element(By.CSS_SELECTOR, ' div:nth-child(5) > div.mt-5 > div > div:nth-child(4)').text.split('Postiosoite')[1].replace('\n','')
                                except:
                                    address = ''
                                    pass
                                try:
                                    zipcode = each_awardee.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.mt-5 > div > div:nth-child(5)').text.split('Postinumero')[1].replace('\n','')
                                except:
                                    zipcode = ''
                                    pass

                                try:
                                    district = each_awardee.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.mt-5 > div > div:nth-child(6)').text.split('Postitoimipaikka')[1].replace('\n','')
                                except:
                                    district = ''
                                    pass

                                try:
                                    country = each_awardee.find_element(By.CSS_SELECTOR, 'div:nth-child(5) > div.mt-5 > div > div:nth-child(7)').text.split('Maa')[1].replace('\n','') 
                                except:
                                    country = ''
                                    pass

                                try:
                                    award_details_data.address = address +' '+zipcode+' '+district+' '+ country
                                except:
                                    pass

                                try:
                                    grossawardvaluelc = each_awardee.find_element(By.CSS_SELECTOR,'div:nth-child(4)').text
                                    grossawardvaluelc = grossawardvaluelc.replace('\n','')
                                    grossawardvaluelc = grossawardvaluelc.replace(' ','')
                                    pattern = '\d+EUR'
                                    grossawardvaluelc = re.findall(pattern,grossawardvaluelc)
                                    grossawardvaluelc = str(grossawardvaluelc)
                                    grossawardvaluelc = re.findall('\d+',grossawardvaluelc)[0]      
                                    award_details_data.grossawardvaluelc = float(grossawardvaluelc)
                                    award_details_data.grossawardvalueeuro = award_details_data.grossawardvaluelc 
                                except Exception as e:
                                    logging.info("Exception in grossawardvaluelc: {}".format(type(e).__name__))
                                    pass

                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)

                    except:
                        logging.info("Exception in award details: {}".format(type(e).__name__))
                        pass

                    lot_details_data.lot_details_cleanup()
                    notice_data.lot_details.append(lot_details_data)
                    lot_number+=1

        except Exception as e:
            logging.info("Exception in lot_details: {}".format(type(e).__name__)) 
            pass


        try:                          
            customer_text = page_details2.find_element(By.CSS_SELECTOR,'div.container > div > div > div > div > div:nth-child(3) > div > div').text 
            customer_details_data = customer_details()

            customer_details_data.org_name = customer_text.split("Virallinen nimi")[1].split("\n")[1].strip()

            try:
                customer_details_data.postal_code = customer_text.split("Postinumero")[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass


            try:
                Postiosoite = customer_text.split("Postiosoite")[1].split("\n")[1].strip()
                Postinumero = customer_details_data.postal_code
                Postitoimipaikka = customer_text.split("Postitoimipaikka")[1].split("\n")[1].strip()
                Maa = customer_text.split("Maa")[1].split("\n")[1].strip()

                customer_details_data.org_address = Postiosoite+' '+Postinumero+' '+Postitoimipaikka+' '+Maa  
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_email = customer_text.split("Sähköpostiosoite")[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_website = customer_text.split("URL")[1].split("\n")[1].strip()  
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.customer_nuts = customer_text.split("NUTS-koodi")[1].split("\n")[1].strip()
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            try:   
                customer_details_data.contact_person = page_details3.find_element(By.XPATH, '(//*[contains(text(),"Nimi")])[3]//following::div[2]').text 
            except Exception as e:
                logging.info("Exception in contact_person: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'FI'
            customer_details_data.org_language = 'FI'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass



    else:
        logging.info('format 2') 

        try:
            notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#main > div').get_attribute("outerHTML")                     
        except:
            notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

        try:
            local_description = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankinnan kuvaus")]//following::div[1]').text
            notice_data.local_description = local_description[:4990]
        except Exception as e:
            logging.info("Exception in local_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_summary_english = GoogleTranslator(source='auto', target='en').translate(notice_data.local_description)  
        except Exception as e:
            logging.info("Exception in notice_summary_english: {}".format(type(e).__name__))
            pass

        try:
            notice_data.type_of_procedure_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Menettelyn tyyppi")]//following::div[1]').text
            type_of_procedure = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
            notice_data.type_of_procedure = fn.procedure_mapping("assets/fi_hanki_procedure.csv",type_of_procedure)
        except Exception as e:
            logging.info("Exception in type_of_procedure_actual: {}".format(type(e).__name__))
            pass

        try:
            notice_contract_type = page_details.find_element(By.XPATH, '//*[contains(text(),"Pääasiallinen hankintalaji")]//following::div[1]/p').text  

            notice_data.contract_type_actual =  notice_contract_type 

            if "Urakat" in notice_contract_type:
                notice_data.notice_contract_type = 'Works'
            elif "Tavarat" in notice_contract_type:
                notice_data.notice_contract_type = 'Supply'
            elif "Palvelut" in notice_contract_type:
                notice_data.notice_contract_type = 'Service'
            else:
                pass
        except Exception as e:
            logging.info("Exception in notice_contract_type: {}".format(type(e).__name__))
            pass


        try:              
            cpvs_data = cpvs()
            cpv_code = page_details.find_element(By.XPATH, '//*[contains(text(),"Hankintanimikkeistö (CPV-koodi)")]//following::div[1]').text   
            cpvs_data.cpv_code = cpv_code.split('(')[1].split(')')[0]
            notice_data.class_at_source = 'CPV'
            notice_data.cpv_at_source = cpvs_data.cpv_code 

            cpvs_data.cpvs_cleanup()
            notice_data.cpvs.append(cpvs_data)
        except Exception as e:
            logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
            pass


        try:              
            for single_record in page_details.find_elements(By.CSS_SELECTOR, 'table.table > tbody > tr > td:nth-child(2)'):
                attachments_data = attachments()

                attachments_data.file_name = single_record.find_element(By.CSS_SELECTOR, 'a').text 

                try:
                    attachments_data.file_type = attachments_data.file_name[-3:]
                except Exception as e:
                    logging.info("Exception in file_type: {}".format(type(e).__name__))
                    pass

                attachments_data.external_url = page_details.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass



        try:             
            customer_details_data = customer_details()

            customer_details_data.org_name = page_details2.find_element(By.XPATH, '//*[contains(text(),"Organisaation virallinen nimi")]//following::div[1]').text
            try:
                customer_details_data.postal_code = page_details2.find_element(By.XPATH, '//*[contains(text(),"Postinumero")]//following::div[1]').text  
            except Exception as e:
                logging.info("Exception in postal_code: {}".format(type(e).__name__))
                pass

            try:

                Postiosoite = page_details2.find_element(By.XPATH, '//*[contains(text(),"Postiosoite")]//following::div[1]').text  
                Postinumero = customer_details_data.postal_code

                Postitoimipaikka = page_details2.find_element(By.XPATH, '//*[contains(text(),"Postitoimipaikka")]//following::div[1]').text  

                Maa = page_details2.find_element(By.XPATH, '//*[contains(text(),"Maa")]//following::div[1]').text  

                Aluekoodi = page_details2.find_element(By.XPATH, '//*[contains(text(),"Aluekoodi")]//following::div[1]').text  

                customer_details_data.org_address = Postiosoite+' '+Postinumero+' '+Postitoimipaikka+' '+Maa+' '+Aluekoodi
            except Exception as e:
                logging.info("Exception in org_address: {}".format(type(e).__name__))  
                pass

            try:
                customer_details_data.org_email = page_details2.find_element(By.XPATH, '//*[contains(text(),"Organisaation sähköpostiosoite")]//following::div[1]').text 
            except Exception as e:
                logging.info("Exception in org_email: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_website = page_details2.find_element(By.XPATH, '//*[contains(text(),"Verkko-osoite")]//following::div[1]').text  
            except Exception as e:
                logging.info("Exception in org_website: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.org_phone = page_details3.find_element(By.XPATH, '//*[contains(text(),"Organisaation puhelinnumero")]//following::div[1]').text 
            except Exception as e:
                logging.info("Exception in org_phone: {}".format(type(e).__name__))
                pass

            try:
                customer_details_data.customer_nuts = page_details2.find_element(By.XPATH, '//*[contains(text(),"Pääasiallinen toimiala")]//following::div[1]').text 
            except Exception as e:
                logging.info("Exception in customer_nuts: {}".format(type(e).__name__))
                pass

            customer_details_data.org_country = 'FI'
            customer_details_data.org_language = 'FI'
            customer_details_data.customer_details_cleanup()
            notice_data.customer_details.append(customer_details_data)
        except Exception as e:
            logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
            pass

        try:
            Tulokset_url = WebDriverWait(page_details, 60).until(EC.presence_of_element_located((By.XPATH, '//a[contains(text(),"Tulokset")]'))).get_attribute("href")                     
            fn.load_page(page_details4,Tulokset_url,100)
            time.sleep(3)
            lot=[]
            award=[]
            for single_record1 in page_details4.find_elements(By.CSS_SELECTOR, '#main > div > div.container > div > div.col-md.main-content > div > div.d-print-none > div > table > tbody > tr a'):
                lot.append(single_record1.text)

            
            for single_record2 in page_details4.find_elements(By.CSS_SELECTOR, '#main > div > div.container > div > div.col-md.main-content > div > div.d-print-none > table > tbody > tr span span:nth-child(2)'):
                award.append(single_record2.text)
            for awards,lots in zip(award,lot):  
                lot_details_data = lot_details()
                lot_details_data.lot_number = 1  
                lot_details_data.lot_title = lots                                               
                lot_details_data.lot_title_english = GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)                                             
                lot_details_data.contract_type = notice_data.notice_contract_type 
                lot_details_data.lot_contract_type_actual  
                award_details_data = award_details()

                award_details_data.bidder_name = awards
                award_details_data.award_details_cleanup()
                lot_details_data.award_details.append(award_details_data)                                          
                                                    
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
arguments= ['--incognito','ignore-certificate-errors','allow-insecure-localhost','--start-maximized']
page_main = fn.init_chrome_driver() 
page_details = fn.init_chrome_driver() 
page_details1 = fn.init_chrome_driver()
page_details2 = fn.init_chrome_driver()
page_details3 = fn.init_chrome_driver()
page_details4 = fn.init_chrome_driver()


try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    urls = ['https://www.hankintailmoitukset.fi/fi/search'] 
    for url in urls:
        fn.load_page(page_main, url, 50)
        logging.info('----------------------------------')
        logging.info(url)
        
        clk=page_main.find_element(By.XPATH,'//*[@id="main"]/div/div[1]/div[1]/div[2]/div[2]/div[2]/div[3]/div/div/label')
        page_main.execute_script("arguments[0].click();",clk)
        clk=page_main.find_element(By.CSS_SELECTOR,'#main > div > div.search-header.d-flex.justify-content-center.flex-column > div.pt-5.container > div.notice-filter-buttons.bg-white.mb-3.row.p-0 > div.notice-group.col-12.col-xl-9.d-flex.flex-column.pt-5.lift-right > div.row.px-1.px-md-3.mb-4 > div.col-12.col-md-4.py-3.pt-md-3.type-button.border-right-0.middle > div > div > label')
        page_main.execute_script("arguments[0].click();",clk)
        for scroll in range(6):
            Näytä_lisää = WebDriverWait(page_main, 80).until(EC.element_to_be_clickable((By.XPATH,'//*[@id="main"]/div/div[2]/div[1]/div/div[3]/button/span')))
            page_main.execute_script("arguments[0].click();",Näytä_lisää)
            time.sleep(3)
        
        try:
            rows = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#main > div > div.search-wrapper.d-flex > div.search-results.container > div > table > tbody tr')))
            length = len(rows)
            for records in range(0,length):
                tender_html_element = WebDriverWait(page_main, 80).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#main > div > div.search-wrapper.d-flex > div.search-results.container > div > table > tbody tr')))[records]
                extract_and_save_notice(tender_html_element)
                if notice_count >= MAX_NOTICES:
                    break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
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
    page_details1.quit()
    page_details2.quit()
    page_details3.quit()
    page_details4.quit()
    output_json_file.copyFinalJSONToServer(output_json_folder)
 
