import gec_common.common_eprocure as common_eprocure

from gec_common import log_config
SCRIPT_NAME = 'in_tendersutl'
log_config.log(SCRIPT_NAME)

domain_url = 'https://tendersutl.gov.in/nicgep'


common_eprocure.eprocure(SCRIPT_NAME,domain_url)
