import gec_common.common_eprocure as common_eprocure

from gec_common import log_config
SCRIPT_NAME = 'in_mahatenders'
log_config.log(SCRIPT_NAME)

domain_url = 'https://mahatenders.gov.in/nicgep'

org_state = 'Maharashtra'

common_eprocure.eprocure(SCRIPT_NAME,domain_url,org_state)
