from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class WinnDixieUSSpider(Spider):
    """
    This brand is owned by Southeastern Grocers (https://www.segrocers.com)
    who reuse the same store finder method for their other brand
    Harveys Supermarkets (spider: harveys_supermarkets_us).
    """
    name = "winn_dixie_us"
    item_attributes = {
        "brand": "Winn-Dixie",
        "brand_wikidata": "Q1264366",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.winndixie.com"]
    start_urls = ["https://www.winndixie.com/V2/storelocator/getStores?search=jacksonville,%20fl&strDefaultMiles=1000&filter="]
    user_agent = BROWSER_DEFAULT

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], method="POST")

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.json():
            item = DictParser.parse(feature)
            item["ref"] = str(feature.get("StoreCode", ""))
            item["branch"] = feature.get("StoreName")
            item.pop("name", None)
            item["street_address"] = clean_address([feature["Address"].get("AddressLine1"), feature["Address"].get("AddressLine2")])
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(feature.get("WorkingHours", ""))
            item["website"] = "https://" + self.allowed_domains[0] + "/storedetails/" + item["city"].lower().replace(" ", "-") + "/" + item["state"].lower() + "?search=" + item["ref"].lower()
            yield item
