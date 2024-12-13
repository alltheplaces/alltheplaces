import scrapy
from geonamescache import GeonamesCache

from locations.dict_parser import DictParser


class FloorAndDecorSpider(scrapy.Spider):
    name = "floor_and_decor"
    item_attributes = {"brand": "Floor and Decor", "brand_wikidata": "Q56280964"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for state in GeonamesCache().get_us_states().keys():
            yield scrapy.FormRequest(
                url="https://www.flooranddecor.com/on/demandware.store/Sites-floor-decor-Site/default/Stores-GetStores?ajax=true",
                formdata={"dwfrm_storeLocator_search": state, "dwfrm_storeLocator_radius": "300"},
            )

    def parse(self, response):
        for store in response.json()["stores"]["storesList"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.flooranddecor.com/" + store.get("detailsLink")
            yield item
