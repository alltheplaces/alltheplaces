from requests import __version__ as REQUESTS_VERSION
from scrapy import __version__ as SCRAPY_VERSION

from locations import __version__ as ATP_VERSION
from locations.settings import BOT_NAME

FIREFOX_ESR_140 = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
FIREFOX_ESR_LATEST = FIREFOX_ESR_140

FIREFOX_141 = "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0"
FIREFOX_LATEST = FIREFOX_141

CHROME_139 = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
CHROME_LATEST = CHROME_139

BROWSER_DEFAULT = FIREFOX_ESR_LATEST

# Wikimedia sites (including Wikidata) have a policy that automated bots
# should send a User-Agent containing the string "Bot".
# https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en
BOT_USER_AGENT_SCRAPY = f"{BOT_NAME}/{ATP_VERSION} (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) AllThePlacesBot/{ATP_VERSION} framework/{SCRAPY_VERSION}"
BOT_USER_AGENT_REQUESTS = f"{BOT_NAME}/{ATP_VERSION} (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) AllThePlacesBot/{ATP_VERSION} python-requests/{REQUESTS_VERSION}"
