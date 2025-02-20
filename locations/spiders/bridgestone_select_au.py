from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.structured_data_spider import StructuredDataSpider


class BridgestoneSelectAUSpider(JSONBlobSpider, StructuredDataSpider):
    name = "bridgestone_select_au"
    item_attributes = {"brand": "Bridgestone", "brand_wikidata": "Q179433"}
    allowed_domains = ["www.bridgestone.com.au"]
    start_urls = ["https://www.bridgestone.com.au//sxa/xsearch/xresults/?l=en&s={8FFB68F0-7F99-44D1-BEB1-69EC32785078}&itemid={294A6BF3-F714-43C8-985C-6B2FDF0EE154}&sig=store-listing-page&p=500&e=0&o=Title%2CAscending&v={80EF6842-A3C2-4FDB-8F88-60EE446DA4A4}"]
    locations_key = "Results"

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Request]:
        for feature in feature_array:
            yield Request(url=feature["Url"], callback=self.parse_sd)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict):
        item["branch"] = item.pop("name").removeprefix("Bridgestone Select ").removeprefix("Bridgestone Service ")
        item.pop("facebook", None)
        apply_category(Categories.SHOP_TYRES, item)
        yield item
