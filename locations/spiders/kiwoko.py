from scrapy import Spider

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class KiwokoSpider(Spider):
    name = "kiwoko"
    item_attributes = {"brand": "Kiwoko", "brand_wikidata": "Q121435937"}
    start_urls = [
        "https://www.kiwoko.com/on/demandware.store/Sites-KiwokoES-Site/default/Stores-FindStores?radius=300000",
        "https://www.kiwoko.pt/on/demandware.store/Sites-KiwokoPT-Site/default/Stores-FindStores?showMap=true&radius=300000",
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["website"] = response.urljoin(f'/{location["ID"]}.html')
            item["street_address"] = clean_address([location["address1"], location["address2"]])

            yield item
