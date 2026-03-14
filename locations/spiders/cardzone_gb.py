from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class CardzoneGBSpider(JSONBlobSpider):
    name = "cardzone_gb"
    item_attributes = {"brand": "Cardzone", "brand_wikidata": "Q123019897"}
    start_urls = [
        "https://cardzoneltd.com/wp-admin/admin-ajax.php?action=store_search&lat=52.95402&lng=-1.15499&max_results=300&search_radius=605&autoload=1"
    ]
    brands = {
        "Cardzone": {"brand": "Cardzone", "brand_wikidata": "Q123019897"},
        "Mooch": {"brand": "Mooch", "brand_wikidata": "Q129256553"},
        "Paper Kisses": {"brand": "Paper Kisses", "brand_wikidata": "Q128803615"},
        "Hallmark": {"brand": "Hallmark", "brand_wikidata": "Q1521910"},
        "Yankee Candle": {"brand": "Yankee Candle", "brand_wikidata": "Q8048733"},
        "Card Centre": {"brand": "Card Centre", "brand_wikidata": "Q129258021"},
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["store"]
        for brand_key in self.brands.keys():
            if item["name"].startswith(brand_key):
                item.update(self.brands[brand_key])

        item.pop("addr_full", None)
        item["street_address"] = clean_address([feature["address"], feature["address2"]])
        yield item
