import gec_common.common_eprocure as common_eprocure
from gec_common import log_config
SCRIPT_NAME = 'in_andaman_eproc'
log_config.log(SCRIPT_NAME)

domain_url = 'https://eprocure.andaman.gov.in/nicgep'

org_state = 'Andaman and Nicobar Islands'

common_eprocure.eprocure(SCRIPT_NAME,domain_url,org_state)
