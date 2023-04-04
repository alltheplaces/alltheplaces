import chompjs
from scrapy.http import FormRequest

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class TimberlandZASpider(AmastyStoreLocatorSpider):
    name = "timberland_za"
    item_attributes = {"brand": "Timberland", "brand_wikidata": "Q1539185"}
    start_urls = ["https://timberland.co.za/amlocator/index/ajax/"]

    def start_requests(self):
        formdata = {
            "lat": "",
            "lng": "",
            "radius": "",
            "mapId": "amlocator-map-canvas642c14a7bc54a",
            "storeListId": "amlocator_store_list642c14a7bd651",
            "product": "",
            "category": "",
            "attributes": "",
        }
        for url in self.start_urls:
            yield FormRequest(url=url, formdata=formdata, headers={"X-Requested-With": "XMLHttpRequest"}, method="POST")
