import json

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


# There is also API to get details of one store
# e.g. https://jysk.pl/services/store/get/P243
# I haven't used it because Jysk easily bans IP
# The same issue with sitemap and parsing sites for each store
class JyskSpider(Spider):
    name = "jysk"
    item_attributes = {"brand": "JYSK", "brand_wikidata": "Q138913"}
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    start_urls = [
        # "https://jysk.ae/find-store",  # few stores, different website format
        # "https://jysk.al/public/store",  # few stores, different website format
        "https://jysk.at/filialen",
        # "https://jysk.az/az/store.html",  # few stores, different website format
        "https://jysk.ba/stores-locator",
        "https://jysk.be/nl/stores-locator",
        "https://jysk.bg/magazini",
        "https://jysk.ch/de/filialen",
        # "https://jysk.com.kw/store-locator",  # few stores, different website format
        # "https://jysk.com.mt/stores-and-opening-hours/",  # few stores, different website format
        "https://jysk.com.tr/magazalari-bulun",
        "https://jysk.co.uk/stores-and-opening-hours",
        "https://jysk.cz/prodejny",
        "https://jysk.de/filialen",
        "https://jysk.dk/butikker-og-abningstider",
        "https://jysk.es/tiendas",
        "https://jysk.fi/myymalat",
        "https://jysk.fr/magasins",
        # "https://jysk.ge/shop/",  # few stores, different website format
        "https://jysk.gr/stores-locator",
        "https://jysk.hr/trgovine",
        "https://jysk.hu/aruhazak",
        "https://jysk.ie/stores-and-opening-hours",
        # "https://jysk.is/thjonusta/opnunartimar/",  # few stores, different website format
        # "https://jysk-ks.com/public/store",  # few stores, different website format
        # "https://jysk.md/store.html?lang=ro",  # different website format
        # "https://jysk.me/prodavnice/",  # few stores, different website format
        # "https://jysk.mk/public/store",  # few stores, different website format
        "https://jysk.nl/winkels",
        "https://jysk.no/butikker",
        "https://jysk.pl/znajdz-sklep",
        "https://jysk.pt/lojas",
        "https://jysk.ro/magazinele-jysk",
        "https://jysk.rs/prodavnice",
        "https://jysk.se/butiker",
        "https://jysk.si/trgovine-odpiralni-casi",
        "https://jysk.sk/predajne",
        "https://jysk.ua/stores-locator",
        # "https://jysk.vn/he-thong-cua-hang",  # different website format
        # "https://www.jysk.ca/storelocator/",  # different website format
        # I cannot find store locator for lt/lv/ee (different website format)
        # "https://www.jysk.lt/",
        # "https://www.jysk.lv/",
        # "https://www.jysk.ee/",
    ]

    def parse(self, response: Response, **kwargs):
        data = json.loads(
            response.xpath("//div[@data-jysk-react-component='StoresLocatorLayout']/@data-jysk-react-properties").get()
        )
        for store in data["storesCoordinates"]:
            item = DictParser.parse(store)
            item["website"] = response.urljoin(store["url"])
            yield item
