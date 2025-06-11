import requests
import scrapy

import locations
from locations import settings

FIREFOX_ESR_128 = "Mozilla/5.0 (Linux x86_64; rv:128.6) Gecko/20100101 Firefox/128.6"
FIREFOX_ESR_LATEST = FIREFOX_ESR_128

FIREFOX_136 = "Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"
FIREFOX_LATEST = FIREFOX_136

CHROME_134 = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
CHROME_LATEST = CHROME_134

BROWSER_DEFAULT = FIREFOX_ESR_LATEST

# Wikimedia sites (including Wikidata) have a policy that automated bots
# should send a User-Agent containing the string "Bot".
# https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en
BOT_USER_AGENT_SCRAPY = f"{settings.BOT_NAME}/{locations.__version__} (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) AllThePlacesBot/{locations.__version__} framework/{scrapy.__version__}"
BOT_USER_AGENT_REQUESTS = f"{settings.BOT_NAME}/{locations.__version__} (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) AllThePlacesBot/{locations.__version__} python-requests/{requests.__version__}"
