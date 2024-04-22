from datetime import date, datetime, timedelta
import wget
import logging
import gec_common.web_application_properties as application_properties
import os 
from zipfile import ZipFile

logging.basicConfig(level=logging.INFO, format="%(asctime)s, %(levelname)s: %(message)s")

fd_count = 0
th = date.today()- timedelta(1)
threshold = th.strftime('%Y%m%d')
th2 = date.today()#- timedelta(1)
threshold2 = th2.strftime('%Y%m%d')
logging.info("Scraping from or greater than: " + threshold)

download_path = application_properties.TMP_DIR + "/zakupki_down_file/" 
extract_path =  application_properties.TMP_DIR + "/zakupki_extract_file/" 

ftplink = 'ftp://free:free@ftp.zakupki.gov.ru/fcs_regions/'
region_list = ['Adygeja_Resp','Altaj_Resp','Altajskij_kraj','Amurskaja_obl','Arkhangelskaja_obl','Astrakhanskaja_obl','Bajkonur_g','Bashkortostan_Resp','Belgorodskaja_obl','Brjanskaja_obl','Burjatija_Resp','Chechenskaja_Resp','Cheljabinskaja_obl','Chukotskij_AO','Chuvashskaja_Resp','Dagestan_Resp','Evrejskaja_Aobl','Ingushetija_Resp','Irkutskaja_obl','Ivanovskaja_obl','Jamalo-Neneckij_AO','Jaroslavskaja_obl','Kabardino-Balkarskaja_Resp','Kaliningradskaja_obl','Kalmykija_Resp','Kaluzhskaja_obl','Kamchatskij_kraj','Karachaevo-Cherkesskaja_Resp','Karelija_Resp','Kemerovskaja_obl','Khabarovskij_kraj','Khakasija_Resp','Khanty-Mansijskij_AO-Jugra_AO','Kirovskaja_obl','Komi_Resp','Kostromskaja_obl','Krasnodarskij_kraj','Krasnojarskij_kraj','Krim_Resp','Kurganskaja_obl','Kurskaja_obl','Leningradskaja_obl','Lipeckaja_obl','Magadanskaja_obl','Marij_El_Resp','Mordovija_Resp','Moskovskaja_obl','Moskva','Murmanskaja_obl','Neneckij_AO','Nizhegorodskaja_obl','Novgorodskaja_obl','Novosibirskaja_obl','Omskaja_obl','Orenburgskaja_obl','Orlovskaja_obl','Penzenskaja_obl','Permskij_kraj','Primorskij_kraj','Pskovskaja_obl','Rjazanskaja_obl','Rostovskaja_obl','Sakha_Jakutija_Resp','Sakhalinskaja_obl','Samarskaja_obl','Sankt-Peterburg','Saratovskaja_obl','Sevastopol_g','Severnaja_Osetija-Alanija_Resp','Smolenskaja_obl','Stavropolskij_kraj','Sverdlovskaja_obl','Tambovskaja_obl','Tatarstan_Resp','Tjumenskaja_obl','Tomskaja_obl','Tulskaja_obl','Tverskaja_obl','Tyva_Resp','Udmurtskaja_Resp','Uljanovskaja_obl','Vladimirskaja_obl','Volgogradskaja_obl','Vologodskaja_obl','Voronezhskaja_obl','Zabajkalskij_kraj']
utype_list = ['notifications', 'requestquotation']
for region in region_list:
    for utype in utype_list:
        try:
            download_path = application_properties.TMP_DIR + "/zakupki_down_file/"  
            extract_path =  application_properties.TMP_DIR + "/zakupki_extract_file/" 
            URL = ftplink + region + '/' + utype + '/currMonth/' + utype + '_' + region + '_' + threshold + '00_' + threshold2 + '00_001.xml.zip'
            fnn = utype + '_' + region + '_' + threshold + '00_' + threshold2 + '00_001.xml.zip'
            ftp_link = URL.replace('notifications_','notification_')
            fname = fnn.replace('notifications_','notification_')
            fnam = fname.replace('.xml.zip','')            
            logging.info(fname)
            logging.info(ftp_link)
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            elif not os.path.exists(extract_path):
                os.makedirs(extract_path)
            else:
                pass
            dd = wget.download(ftp_link, out=download_path)
            logging.info(dd)
            filename = download_path + fname
            extract_path = extract_path + threshold + '/' + fnam 
            logging.info(extract_path)
            logging.info(filename)
            with ZipFile(filename, 'r') as zObject:
                zObject.extractall(
                path=extract_path )
                zObject.close()
            fd_count += 1
        except:
            logging.info("Failed to load URL: ",str(ftp_link))
            pass
logging.info("Finished processing. Scraped {} notices".format(fd_count))
