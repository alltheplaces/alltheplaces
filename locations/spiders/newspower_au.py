from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.storeify import StoreifySpider


class NewspowerAUSpider(StoreifySpider):
    name = "newspower_au"
    item_attributes = {"brand": "Newspower", "brand_wikidata": "Q120670137"}
    api_key = "newspower-australia.myshopify.com"
    domain = "https://newspower.com.au/"
