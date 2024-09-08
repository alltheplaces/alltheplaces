from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class AlnaturaDESpider(Spider):
    name = "alnatura_de"
    item_attributes = {"brand": "Alnatura", "brand_wikidata": "Q876811", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.alnatura.de"]
    start_urls = ["https://www.alnatura.de/api/sitecore/stores/FindStoresforMap?ElementsPerPage=10000&lat=49.878708&lng=8.646927&radius=10000&Tradepartner=1"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response) -> Iterable[JsonRequest]:
        for feature in response.json()["Payload"]:
            feature_id = feature["Id"]
            yield JsonRequest(url=f"https://www.alnatura.de/api/sitecore/stores/StoreDetails?storeid={feature_id}", meta={"lat": feature.get("Lat"), "lon": feature.get("Lng")}, callback=self.parse_feature)

    def parse_feature(self, response: Response) -> Iterable[Feature]:
        feature = response.json()["Payload"]
        feature["lat"] = response.meta["lat"]
        feature["lon"] = response.meta["lon"]
        item = DictParser.parse(feature)
        item["street_address"] = clean_address([feature.get("Street"), feature.get("AddressExtension")])
        item.pop("street", None)
        if feature.get("StoreDetailPage"):
            item["website"] = "https://www.alnatura.de" + feature["StoreDetailPage"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature.get("OpeningTime", ""))
        yield item
