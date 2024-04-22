import gec_common.common_eprocure as common_eprocure

from gec_common import log_config
SCRIPT_NAME = 'in_midhani'
log_config.log(SCRIPT_NAME)


domain_url = 'https://eprocuremidhani.nic.in/nicgep'


common_eprocure.eprocure(SCRIPT_NAME,domain_url)
