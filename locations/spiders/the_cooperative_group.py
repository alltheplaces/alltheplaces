from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.central_england_cooperative import COOP_FUNERALCARE, set_operator


class TheCooperativeGroupSpider(JSONBlobSpider):
    name = "the_cooperative_group"
    item_attributes = {"brand": "The Co-operative Group", "brand_wikidata": "Q117202"}
    start_urls = ["https://www.coop.co.uk/store-finder/api/locations/food/?&distance=3000&min_distance=0&min_results=1&format=json&page_size=2500"]
    locations_key = "results"
    drop_attributes = {"facebook", "twitter"}


   def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["lat"],item["lon"] = feature["position"]["y"],feature["position"]["x"]
        item["website"] = "https://www.coop.co.uk" + item["website"]
        item["street_address"] = merge_address_lines([feature["street_address"],feature["street_address2"],feature["street_address3"]])
        item["branch"] = item.pop("name")
        item["name"] = feature["society"]
        yield item
