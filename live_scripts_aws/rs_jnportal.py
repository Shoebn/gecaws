from gec_common.gecclass import *
import logging
from gec_common import log_config
SCRIPT_NAME = "rs_jnportal"
log_config.log(SCRIPT_NAME)
import re
import jsons
import time
from datetime import date, datetime, timedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from deep_translator import GoogleTranslator
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
import gec_common.OutputJSON
from gec_common import functions as fn

NOTICE_DUPLICATE_COUNT = 0
MAX_NOTICES_DUPLICATE = 4
MAX_NOTICES = 2000
notice_count = 0
SCRIPT_NAME = "rs_jnportal"

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# #Note : some time amendment notice and contract award data comes in spn.. so if the "The name of the ad" get below , than skip this data from notice type 4(spn) and move in respective notice type giben below 
# "Correction - notification of changes or additional information"  = "notice type 16"
# Notice on the award of contracts concluded on the basis of a framework agreement / dynamic procurement system  = "notice type 7"


#  1)  to explore details go to url : "https://jnportal.ujn.gov.rs/oglasi-svi"
#  2)   click on "Поступци јавних набавки"  (left side drop down)
#  3)   select "Огласи о јавној набавци" option 
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

output_json_file = gec_common.OutputJSON.OutputJSON(SCRIPT_NAME)
output_json_folder = "jsonfile"
def extract_and_save_notice(tender_html_element):
    global notice_count
    global notice_data
    
    notice_data = tender()    

    notice_data.script_name = 'rs_jnportal'

    notice_data.main_language = 'SR'

    performance_country_data = performance_country()
    performance_country_data.performance_country = 'RS'
    notice_data.performance_country.append(performance_country_data)

    notice_data.procurement_method = 4

    notice_data.currency = 'RSD'

        # Onsite Field -if the following field "Назив огласа" (selector : "#dx-col-34 > div.dx-datagrid-text-content.dx-text-content-alignment-left" ) contains  "Јавни позив" keyword then take as a notice_type 4
        # Onsite Comment -None

    notice_data.class_at_source = "CPV"

    types = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(7)').text
    
    if "Обавештење о додели уговора" in types:
        notice_data.notice_type = 7  
        notice_data.script_name = 'rs_jnportal_ca'

         # Onsite Field -Назив огласа
    # Onsite Comment -None

        try:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

#     # Onsite Field -Број огласа
#     # Onsite Comment -None

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        # Onsite Field -Назив набавке
        # Onsite Comment -None

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(5)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Датум објаве
        # Onsite Comment -None

        try:              
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'a.dx-icon-download.icon'):
                attachments_data = attachments()
                attachments_data.file_name = "Tender Documents"

                attachments_data.external_url = single_record.get_attribute('href')
                
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
            fn.load_page_expect_xpath(page_details,notice_data.notice_url,'//*[contains(text(),"Наручилац")]',80)
            time.sleep(10)
            logging.info(notice_data.notice_url)


            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#uiContent').get_attribute("outerHTML")                     
            except:
                notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

            try:
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                if 'Радови' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Добра' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
                elif 'Услуге' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
                pass

            try:
                notice_data.type_of_procedure_actual =  page_details.find_element(By.XPATH, "//*[contains(text(),'Врста поступка')]//following::span[1]").text
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/rs_jnportal_procedure.csv",type_of_procedure_actual)
            except:
                pass

            try:
                publish_date = page_details.find_element(By.XPATH, ' //*[@id="tenderNoticesContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr[last()-1]/td[7]').get_attribute('innerHTML')
                publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return

            # Onsite Field -Процењена вредност
            # Onsite Comment -None

            try:
                est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Процењена вредност")]//following::td[1]/span').text
                est_amount = re.sub("[^\d\.\,]", "",est_amount)
                est_amount =est_amount.replace('.','').replace(',','.')
                notice_data.est_amount = float(est_amount.strip())
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

            try:
                notice_data.related_tender_id =  page_details.find_element(By.XPATH, "//*[contains(text(),'Референтни број')]//following::span[1]").text
            except:
                try:
                    notice_data.related_tender_id =  page_details.find_element(By.XPATH, '//*[@id="tenderBasicInfoPanelTemplate"]').text.split('Референтни број')[1].split('\n')[0]
                except:
                    pass

            try:
                notice_data.grossbudgetlc = notice_data.est_amount
            except:
                pass

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_country = 'RS'
                customer_details_data.org_language = 'SR'
                # Onsite Field -Наручилац
                # Onsite Comment -None

                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(4)').text

                # Onsite Field -Локација наручиоца
                # Onsite Comment -None

                try:
                    customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Локација наручиоца')]//following::td[1]").text
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass

        # Onsite Field -Ставка плана на основу које је набавка покренута
        # Onsite Comment -None

            try:              
                cpvs_data = cpvs()
                # Onsite Field -ЦПВ
                # Onsite Comment -None

                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer > div > div.dx-datagrid-rowsview > div > div > div.dx-scrollable-content > div > table > tbody > tr.dx-row.dx-data-row > td:nth-child(5)').text.split("-")[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass

            # Onsite Field -ЦПВ
            # Onsite Comment -None

            try:
                notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer > div > div.dx-datagrid-rowsview > div > div > div.dx-scrollable-content > div > table > tbody > tr.dx-row.dx-data-row > td:nth-child(5)').text.split("-")[0].strip()
            except Exception as e:
                logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                pass

            try:
                range_lot=page_details.find_element(By.CSS_SELECTOR, '#uiContent').text
            except:
                pass

            try: 
                if "За партију" in range_lot:
                    time.sleep(3)

                    if 'Одлуке о додели оквирног споразума'in range_lot:

                        award_data=page_details.find_element(By.CSS_SELECTOR, '#tenderDetailFrameworkAgreementDecisionsPanel > div > div')
                        awards =[]
                        for award in award_data.find_elements(By.CSS_SELECTOR, 'tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(5)'):
                            awards.append(award.text)


                        time.sleep(5)
                        lot=[]
                        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsContainer div.dx-scrollable table td.wrappedColumnMobile')[:-1]:
                            lot.append(single_record.text)

                        lot_number=1 
                        for award_data,lot_data in zip(awards,lot):
                            lot_details_data = lot_details()
                            lot_details_data.lot_number=lot_number
                            lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                            lot_details_data.lot_title = lot_data
                            lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)



                            try:
                                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                                if 'Радови' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Works'
                                elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Service'
                                elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                    lot_details_data.contract_type = 'Supply'
                                else:
                                    pass
                            except Exception as e:
                                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                                pass





                            try:
                                award_details_data = award_details()

                                award_details_data.bidder_name = award_data


                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                            except Exception as e:
                                logging.info("Exception in award_details: {}".format(type(e).__name__))
                                pass


                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number+=1

                    elif 'Одлуке о додели' in range_lot:

                        award_data=page_details.find_element(By.CSS_SELECTOR, '#tenderDetailAwardDecisionsPanel > div')

                        awards2 =[]
                        for award in award_data.find_elements(By.CSS_SELECTOR, 'tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(5)'):
                            awards2.append(award.text)



                        time.sleep(5)
                        lot2=[]
                        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsContainer div.dx-scrollable table td.wrappedColumnMobile')[:-1]:
                            lot2.append(single_record.text)


                        lot_number=1 
                        for award_data,lot_data in zip(awards2,lot2):
                            lot_details_data = lot_details()
                            lot_details_data.lot_number=lot_number
                            lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                            lot_details_data.lot_title = lot_data
                            lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)


                            try:
                                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                                if 'Радови' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Works'
                                elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Service'
                                elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                    lot_details_data.contract_type = 'Supply'
                                else:
                                    pass
                            except Exception as e:
                                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                                pass    


                            try:
                                award_details_data = award_details()

                                award_details_data.bidder_name = award_data


                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                            except Exception as e:
                                logging.info("Exception in award_details: {}".format(type(e).__name__))
                                pass


                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number+=1
                else:

                    time.sleep(5)
                    if 'Одлуке о додели оквирног споразума'in range_lot:

                        award_data=page_details.find_element(By.CSS_SELECTOR, '#tenderDetailFrameworkAgreementDecisionsPanel > div > div')
                        awards =[]
                        for award in award_data.find_elements(By.CSS_SELECTOR, 'tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(4)'):
                            awards.append(award.text)



                        time.sleep(5)
                        lot=[]
                        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsContainer div.dx-scrollable table td.wrappedColumnMobile')[:-1]:
                            lot.append(single_record.text)

                        lot_number=1 
                        for award_data,lot_data in zip(awards,lot):
                            lot_details_data = lot_details()
                            lot_details_data.lot_number=lot_number
                            lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                            lot_details_data.lot_title = lot_data
                            lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)



                            try:
                                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                                if 'Радови' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Works'
                                elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Service'
                                elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                    lot_details_data.contract_type = 'Supply'
                                else:
                                    pass
                            except Exception as e:
                                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                                pass

                            try:
                                award_details_data = award_details()

                                award_details_data.bidder_name = award_data


                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                            except Exception as e:
                                logging.info("Exception in award_details: {}".format(type(e).__name__))
                                pass


                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number+=1

                    elif 'Одлуке о додели' in range_lot:

                        award_data=page_details.find_element(By.CSS_SELECTOR, '#tenderDetailAwardDecisionsPanel > div')

                        awards2 =[]
                        for award in award_data.find_elements(By.CSS_SELECTOR, 'tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(4)'):
                            awards2.append(award.text)


                        time.sleep(5)
                        lot2=[]
                        for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsContainer div.dx-scrollable table td.wrappedColumnMobile')[:-1]:
                            lot2.append(single_record.text)


                        lot_number=1 
                        for award_data,lot_data in zip(awards2,lot2):
                            lot_details_data = lot_details()
                            lot_details_data.lot_number=lot_number
                            lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                            lot_details_data.lot_title = lot_data
                            lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)



                            try:
                                lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                                if 'Радови' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Works'
                                elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                     lot_details_data.contract_type = 'Service'
                                elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                    lot_details_data.contract_type = 'Supply'
                                else:
                                    pass
                            except Exception as e:
                                logging.info("Exception in contract_type: {}".format(type(e).__name__))
                                pass                        


                            try:
                                award_details_data = award_details()

                                award_details_data.bidder_name = award_data


                                award_details_data.award_details_cleanup()
                                lot_details_data.award_details.append(award_details_data)
                            except Exception as e:
                                logging.info("Exception in award_details: {}".format(type(e).__name__))
                                pass


                            lot_details_data.lot_details_cleanup()
                            notice_data.lot_details.append(lot_details_data)
                            lot_number+=1

            except Exception as e:
                logging.info("Exception in award_details: {}".format(type(e).__name__))
                pass
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
#************************************************************************************************************
    elif "Исправка - обавештење о изменама или додатним информацијама" in types:
        notice_data.notice_type = 16   
 
        try:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

#     # Onsite Field -Број огласа
#     # Onsite Comment -None

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        # Onsite Field -Назив набавке
        # Onsite Comment -None

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(5)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Датум објаве
        # Onsite Comment -None


        try:              
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'a.dx-icon-download.icon'):
                attachments_data = attachments()
                attachments_data.file_name = "Tender Documents"
                attachments_data.external_url = single_record.get_attribute('href')
                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
            fn.load_page_expect_xpath(page_details,notice_data.notice_url,'//*[contains(text(),"Наручилац")]',80)
            logging.info(notice_data.notice_url)
            time.sleep(5)


            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#uiContent').get_attribute("outerHTML")                     
            except:
                notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

            try:
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                if 'Радови' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Добра' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
                elif 'Услуге' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
                pass

            try:
                notice_data.type_of_procedure_actual =  page_details.find_element(By.XPATH, "//*[contains(text(),'Врста поступка')]//following::span[1]").text
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/rs_jnportal_procedure.csv",type_of_procedure_actual)
            except:
                pass



            try:
                notice_data.related_tender_id =  page_details.find_element(By.XPATH, "//*[contains(text(),'Референтни број')]//following::span[1]").text
            except:
                try:
                    notice_data.related_tender_id =  page_details.find_element(By.XPATH, '//*[@id="tenderBasicInfoPanelTemplate"]').text.split('Референтни број')[1].split('\n')[0]
                except:
                    pass

            # Onsite Field -Процењена вредност
            # Onsite Comment -None

            try:
                publish_date = page_details.find_element(By.XPATH, ' //*[@id="tenderNoticesContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr[last()-1]/td[7]').get_attribute('innerHTML')
                publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return


            try:
                est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Процењена вредност")]//following::td[1]/span').text
                est_amount = re.sub("[^\d\.\,]", "",est_amount)
                est_amount =est_amount.replace('.','').replace(',','.')
                notice_data.est_amount = float(est_amount.strip())
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

            try:
                notice_data.grossbudgetlc = notice_data.est_amount
            except:
                pass

            # Onsite Field -Рок за подношење
            # Onsite Comment -ref_url : "https://jnportal.ujn.gov.rs/tender-eo/55"

            try:
                notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Рок за подношење")]//following::td[1]/span').text
                notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_country = 'RS'
                customer_details_data.org_language = 'SR'
                # Onsite Field -Наручилац
                # Onsite Comment -None

                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(4)').text

                # Onsite Field -Локација наручиоца
                # Onsite Comment -None

                try:
                    customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Локација наручиоца')]//following::td[1]").text
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass

        # Onsite Field -Ставка плана на основу које је набавка покренута
        # Onsite Comment -None

            try:              
                cpvs_data = cpvs()
                # Onsite Field -ЦПВ
                # Onsite Comment -None

                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer > div > div.dx-datagrid-rowsview > div > div > div.dx-scrollable-content > div > table > tbody > tr.dx-row.dx-data-row > td:nth-child(5)').text.split("-")[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass

            # Onsite Field -ЦПВ
            # Onsite Comment -None

            try:
                notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer > div > div.dx-datagrid-rowsview > div > div > div.dx-scrollable-content > div > table > tbody > tr.dx-row.dx-data-row > td:nth-child(5)').text.split("-")[0].strip()
            except Exception as e:
                logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                pass

        # Onsite Field -Предмет / партије
        # Onsite Comment -None


            try:
                range_lot=page_details.find_element(By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-pager.dx-pager > div > div:nth-child(2)').text
                lot=int(range_lot)
                lot_number=1
                for page_no in range(1,lot+1):                                                                          
                    page_check = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr'))).text
                    rows = WebDriverWait(page_details, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')))
                    length = len(rows)

                    for records in range(0,length-1):
                        single_record = WebDriverWait(page_details, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')))[records]
                        lot_details_data = lot_details()
                        lot_details_data.lot_number=lot_number
                        lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                        lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td.wrappedColumnMobile').text
                        lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc1: {}".format(type(e).__name__))
                            pass
                        try:
                            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                            if 'Радови' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Works'
                            elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Service'
                            elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                lot_details_data.contract_type = 'Supply'
                            else:
                                pass
                        except Exception as e:
                            logging.info("Exception in contract_type: {}".format(type(e).__name__))
                            pass
                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc2: {}".format(type(e).__name__))
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number+=1

                    if lot == page_no:
                        break
                    next_page = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#tenderDetailLotsContainer > div > div.dx-datagrid-pager.dx-pager > div > div:nth-child(2)")))
                    page_details.execute_script("arguments[0].click();",next_page)
                    WebDriverWait(page_details, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr'),page_check))
            except:
                try:                                                                 
                    lot_number=1
                    for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')[:-1]:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual
                    # Onsite Field -Назив td.wrappedColumnMobile   
                    # Onsite Comment -ref_url : "https://jnportal.ujn.gov.rs/tender-eo/188746"

                        lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td.wrappedColumnMobile').text
                        lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                    # Onsite Field -Предмет / партије >> Процењена вредност
                    # Onsite Comment -if this field "Предмет / партије" have more than one lots then use following selkector "#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(4)"   , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/188746"

                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc1: {}".format(type(e).__name__))
                            pass
                        try:
                            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                            if 'Радови' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Works'
                            elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Service'
                            elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                lot_details_data.contract_type = 'Supply'
                            else:
                                pass
                        except Exception as e:
                            logging.info("Exception in contract_type: {}".format(type(e).__name__))
                            pass

                    # Onsite Field -Предмет / партије >> Процењена вредност
                    # Onsite Comment -if this field "Предмет / партије" have only one lot then use following selkector "#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(3)"    ,  ref_url : "https://jnportal.ujn.gov.rs/tender-eo/188748"

                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc  = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc2: {}".format(type(e).__name__))
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                except Exception as e:
                    logging.info("Exception in lot_details: {}".format(type(e).__name__))
                    pass
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass
#*********************************************************************************************************************     

    else:
        notice_data.notice_type = 4   

         # Onsite Field -Назив огласа
    # Onsite Comment -None

        try:
            notice_data.document_type_description = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(7)').text
        except Exception as e:
            logging.info("Exception in document_type_description: {}".format(type(e).__name__))
            pass

        try:
            notice_data.notice_no = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(3)').text
        except Exception as e:
            logging.info("Exception in notice_no: {}".format(type(e).__name__))
            pass

        # Onsite Field -Назив набавке
        # Onsite Comment -None

        try:
            notice_data.local_title = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(5)').text
            notice_data.notice_title = GoogleTranslator(source='auto', target='en').translate(notice_data.local_title)
        except Exception as e:
            logging.info("Exception in local_title: {}".format(type(e).__name__))
            pass

        # Onsite Field -Датум објаве
        # Onsite Comment -None

        try:              
            for single_record in tender_html_element.find_elements(By.CSS_SELECTOR, 'a.dx-icon-download.icon'):
                attachments_data = attachments()
                attachments_data.file_name = "Tender Documents"

                attachments_data.external_url = single_record.get_attribute('href')

                attachments_data.attachments_cleanup()
                notice_data.attachments.append(attachments_data)
        except Exception as e:
            logging.info("Exception in attachments: {}".format(type(e).__name__)) 
            pass

        try:
            notice_data.notice_url = tender_html_element.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > a').get_attribute("href")                     
            fn.load_page_expect_xpath(page_details,notice_data.notice_url,'//*[contains(text(),"Наручилац")]',80)
            logging.info(notice_data.notice_url)

            try:
                notice_data.notice_text += page_details.find_element(By.CSS_SELECTOR, '#uiContent').get_attribute("outerHTML")                     
            except:
                notice_data.notice_text += tender_html_element.get_attribute('outerHTML')

            try:
                notice_data.contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                if 'Радови' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Works'
                elif 'Добра' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Supply'
                elif 'Услуге' in notice_data.contract_type_actual:
                    notice_data.notice_contract_type = 'Service'
                else:
                    pass
            except Exception as e:
                logging.info("Exception in contract_type_actual: {}".format(type(e).__name__))
                pass


            try:
                notice_data.type_of_procedure_actual =  page_details.find_element(By.XPATH, "//*[contains(text(),'Врста поступка')]//following::span[1]").text
                type_of_procedure_actual = GoogleTranslator(source='auto', target='en').translate(notice_data.type_of_procedure_actual)
                notice_data.type_of_procedure = fn.procedure_mapping("assets/rs_jnportal_procedure.csv",type_of_procedure_actual)
            except:
                pass


            try:
                publish_date = page_details.find_element(By.XPATH, '//*[@id="tenderNoticesContainer"]/div/div[6]/div/div/div[1]/div/table/tbody/tr[last()-1]/td[7]').get_attribute('innerHTML')
                publish_date = re.findall('\d+.\d+.\d{4}',publish_date)[0]
                notice_data.publish_date = datetime.strptime(publish_date,'%d.%m.%Y').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.publish_date)
            except Exception as e:
                logging.info("Exception in publish_date: {}".format(type(e).__name__))
                pass

            if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                return

            try:
                notice_data.related_tender_id =  page_details.find_element(By.XPATH, "//*[contains(text(),'Референтни број')]//following::span[1]").text
            except:
                try:
                    notice_data.related_tender_id =  page_details.find_element(By.XPATH, '//*[@id="tenderBasicInfoPanelTemplate"]').text.split('Референтни број')[1].split('\n')[0]
                except:
                    pass

            # Onsite Field -Процењена вредност
            # Onsite Comment -None

            try:
                est_amount = page_details.find_element(By.XPATH, '//*[contains(text(),"Процењена вредност")]//following::td[1]/span').text
                est_amount = re.sub("[^\d\.\,]", "",est_amount)
                est_amount =est_amount.replace('.','').replace(',','.')
                notice_data.est_amount = float(est_amount.strip())
            except Exception as e:
                logging.info("Exception in est_amount: {}".format(type(e).__name__))
                pass

    #     # Onsite Field -Број огласа
    #     # Onsite Comment -None
            try:
                notice_data.grossbudgetlc = notice_data.est_amount
            except:
                pass

            # Onsite Field -Рок за подношење
            # Onsite Comment -ref_url : "https://jnportal.ujn.gov.rs/tender-eo/55"

            try:
                notice_deadline = page_details.find_element(By.XPATH, '//*[contains(text(),"Рок за подношење")]//following::td[1]/span').text
                notice_deadline = re.findall('\d+.\d+.\d{4} \d+:\d+:\d+',notice_deadline)[0]
                notice_data.notice_deadline = datetime.strptime(notice_deadline,'%d.%m.%Y %H:%M:%S').strftime('%Y/%m/%d %H:%M:%S')
                logging.info(notice_data.notice_deadline)
            except Exception as e:
                logging.info("Exception in notice_deadline: {}".format(type(e).__name__))
                pass

            try:              
                customer_details_data = customer_details()
                customer_details_data.org_country = 'RS'
                customer_details_data.org_language = 'SR'
                # Onsite Field -Наручилац
                # Onsite Comment -None

                customer_details_data.org_name = tender_html_element.find_element(By.CSS_SELECTOR, 'div.dx-scrollable-content  td:nth-child(4)').text

                # Onsite Field -Локација наручиоца
                # Onsite Comment -None

                try:
                    customer_details_data.org_city = page_details.find_element(By.XPATH, "//*[contains(text(),'Локација наручиоца')]//following::td[1]").text
                except Exception as e:
                    logging.info("Exception in org_city: {}".format(type(e).__name__))
                    pass

                customer_details_data.customer_details_cleanup()
                notice_data.customer_details.append(customer_details_data)
            except Exception as e:
                logging.info("Exception in customer_details: {}".format(type(e).__name__)) 
                pass

        # Onsite Field -Ставка плана на основу које је набавка покренута
        # Onsite Comment -None

            try:              
                cpvs_data = cpvs()
                # Onsite Field -ЦПВ
                # Onsite Comment -None

                cpvs_data.cpv_code = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer > div > div.dx-datagrid-rowsview > div > div > div.dx-scrollable-content > div > table > tbody > tr.dx-row.dx-data-row > td:nth-child(5)').text.split("-")[0].strip()
                cpvs_data.cpvs_cleanup()
                notice_data.cpvs.append(cpvs_data)
            except Exception as e:
                logging.info("Exception in cpvs: {}".format(type(e).__name__)) 
                pass

            # Onsite Field -ЦПВ
            # Onsite Comment -None

            try:
                notice_data.cpv_at_source = page_details.find_element(By.CSS_SELECTOR, '#planItemsAssociatedGridContainer > div > div.dx-datagrid-rowsview > div > div > div.dx-scrollable-content > div > table > tbody > tr.dx-row.dx-data-row > td:nth-child(5)').text.split("-")[0].strip()
            except Exception as e:
                logging.info("Exception in cpv_at_source: {}".format(type(e).__name__))
                pass

        # Onsite Field -Предмет / партије
        # Onsite Comment -None

            try:
                range_lot=page_details.find_element(By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-pager.dx-pager > div > div:nth-child(2)').text
                lot=int(range_lot)
                lot_number=1
                for page_no in range(1,lot+1):                                                                          
                    page_check = WebDriverWait(page_details, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr'))).text
                    rows = WebDriverWait(page_details, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')))
                    length = len(rows)

                    for records in range(0,length-1):
                        single_record = WebDriverWait(page_details, 50).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated.dx-scrollable-customizable-scrollbars > div > div > div.dx-scrollable-content > div > table > tbody > tr')))[records]
                        lot_details_data = lot_details()
                        lot_details_data.lot_number=lot_number
                        lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual

                        lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td.wrappedColumnMobile').text
                        lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)
                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc1: {}".format(type(e).__name__))
                            pass
                        try:
                            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                            if 'Радови' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Works'
                            elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Service'
                            elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                lot_details_data.contract_type = 'Supply'
                            else:
                                pass
                        except Exception as e:
                            logging.info("Exception in contract_type: {}".format(type(e).__name__))
                            pass
                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc2: {}".format(type(e).__name__))
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number+=1

                    if lot == page_no:
                        break
                    next_page = WebDriverWait(page_details, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#tenderDetailLotsContainer > div > div.dx-datagrid-pager.dx-pager > div > div:nth-child(2)")))
                    page_details.execute_script("arguments[0].click();",next_page)
                    WebDriverWait(page_details, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr'),page_check))
            except:
                try:                                                                 
                    lot_number=1
                    for single_record in page_details.find_elements(By.CSS_SELECTOR, '#tenderDetailLotsContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')[:-1]:
                        lot_details_data = lot_details()
                        lot_details_data.lot_number = lot_number
                        lot_details_data.lot_contract_type_actual= notice_data.contract_type_actual
                    # Onsite Field -Назив td.wrappedColumnMobile   
                    # Onsite Comment -ref_url : "https://jnportal.ujn.gov.rs/tender-eo/188746"

                        lot_details_data.lot_title = single_record.find_element(By.CSS_SELECTOR, 'td.wrappedColumnMobile').text
                        lot_details_data.lot_title_english=GoogleTranslator(source='auto', target='en').translate(lot_details_data.lot_title)

                    # Onsite Field -Предмет / партије >> Процењена вредност
                    # Onsite Comment -if this field "Предмет / партије" have more than one lots then use following selkector "#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(4)"   , ref_url : "https://jnportal.ujn.gov.rs/tender-eo/188746"

                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)

                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc1: {}".format(type(e).__name__))
                            pass

                        try:
                            lot_details_data.lot_contract_type_actual = page_details.find_element(By.XPATH, '//*[contains(text(),"Врста предмета")]//following::td[1]/span').text
                            if 'Радови' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Works'
                            elif 'Услуге' in lot_details_data.lot_contract_type_actual :
                                 lot_details_data.contract_type = 'Service'
                            elif 'Добра' in lot_details_data.lot_contract_type_actual :
                                lot_details_data.contract_type = 'Supply'
                            else:
                                pass
                        except Exception as e:
                            logging.info("Exception in contract_type: {}".format(type(e).__name__))
                            pass

                    # Onsite Field -Предмет / партије >> Процењена вредност
                    # Onsite Comment -if this field "Предмет / партије" have only one lot then use following selkector "#tenderDetailLotsContainer tr.dx-row.dx-data-row.dx-column-lines > td:nth-child(3)"    ,  ref_url : "https://jnportal.ujn.gov.rs/tender-eo/188748"

                        try:
                            lot_grossbudget_lc = single_record.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
                            lot_grossbudget_lc = re.sub("[^\d\.\,]", "",lot_grossbudget_lc)
                            lot_grossbudget_lc = lot_grossbudget_lc.replace('.','').replace(',','.').strip()
                            lot_details_data.lot_grossbudget_lc = float(lot_grossbudget_lc)
                        except Exception as e:
                            logging.info("Exception in lot_grossbudget_lc2: {}".format(type(e).__name__))
                            pass

                        lot_details_data.lot_details_cleanup()
                        notice_data.lot_details.append(lot_details_data)
                        lot_number += 1
                except Exception as e:
                    logging.info("Exception in lot_details: {}".format(type(e).__name__))
                    pass
        except Exception as e:
            logging.info("Exception in notice_url: {}".format(type(e).__name__))
            pass

    notice_data.identifier = str(notice_data.script_name) + str(notice_data.notice_no) + str(notice_data.publish_date) +  str(notice_data.notice_url) +  str(notice_data.local_title) 
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
page_details = webdriver.Chrome(options=options)
try:
    th = date.today() - timedelta(1)
    threshold = th.strftime('%Y/%m/%d')
    logging.info("Scraping from or greater than: " + threshold)
    threshold1 = th.strftime('%Y-%m-%d')
    urls = ['https://jnportal.ujn.gov.rs/oglasi-svi?initFilter=[%22PublishDate%22,%22%3E=%22,%22'+str(threshold1)+'%22]'] 
    
    for url in urls:
        fn.load_page(page_main, url, 60)
        logging.info('----------------------------------')
        logging.info(url)

        try:
            for page_no in range(1,100): 
                page_check = WebDriverWait(page_main, 50).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#searchGridContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr'))).text
                rows = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#searchGridContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')))
                length = len(rows)
                for records in range(0,length-1):
                    tender_html_element = WebDriverWait(page_main, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#searchGridContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr')))[records]
                    extract_and_save_notice(tender_html_element)
                    if notice_count >= MAX_NOTICES:
                        break
    
                    if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                        break
    
                if notice_data.publish_date is not None and notice_data.publish_date < threshold:
                    break
    
                try:   
                    next_page = WebDriverWait(page_main, 50).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"#searchGridContainer > div > div.dx-widget.dx-datagrid-pager.dx-pager > div.dx-pages > div.dx-page-indexes > div.dx-navigate-button.dx-next-button")))
                    page_main.execute_script("arguments[0].click();",next_page)
                    logging.info("Next page")
                    WebDriverWait(page_main, 50).until_not(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#searchGridContainer > div > div.dx-datagrid-rowsview.dx-datagrid-nowrap.dx-scrollable.dx-visibility-change-handler.dx-scrollable-both.dx-scrollable-simulated > div > div > div.dx-scrollable-content > div > table > tbody > tr'),page_check))
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
