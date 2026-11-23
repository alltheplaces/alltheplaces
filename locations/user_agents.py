from requests import __version__ as REQUESTS_VERSION
from scrapy import __version__ as SCRAPY_VERSION

from locations import __version__ as ATP_VERSION
from locations.settings import BOT_NAME

FIREFOX_ESR_153 = "Mozilla/5.0 (X11; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0"
FIREFOX_ESR_LATEST = FIREFOX_ESR_153

FIREFOX_160 = "Mozilla/5.0 (X11; Linux x86_64; rv:160.0) Gecko/20100101 Firefox/160.0"
FIREFOX_LATEST = FIREFOX_160

CHROME_158 = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36"
CHROME_LATEST = CHROME_158

BROWSER_DEFAULT = FIREFOX_ESR_LATEST

# Wikimedia sites (including Wikidata) have a policy that automated bots
# should send a User-Agent containing the string "Bot".
# https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en
BOT_USER_AGENT_SCRAPY = f"{BOT_NAME}/{ATP_VERSION} (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) AllThePlacesBot/{ATP_VERSION} framework/{SCRAPY_VERSION}"
BOT_USER_AGENT_REQUESTS = f"{BOT_NAME}/{ATP_VERSION} (+https://github.com/alltheplaces/alltheplaces; +https://alltheplaces.xyz/) AllThePlacesBot/{ATP_VERSION} python-requests/{REQUESTS_VERSION}"
