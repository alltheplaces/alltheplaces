from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class CoopFuneralGBSpider(JSONBlobSpider):
    name = "coop_funeral_gb"
    item_attributes = {"brand": "The Co-operative Funeralcare", "brand_wikidata": "Q7726521"}
    start_urls = ["https://production.api.fnc.digital.coop.co.uk/branches?page_size=1000"]
    locations_key = "results"
    drop_attributes = {"email", "facebook", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["position"]["y"], feature["position"]["x"]
        item["website"] = "https://www.coop.co.uk" + item["website"]
        item["street_address"] = merge_address_lines(
            [feature["street_address"], feature["street_address2"], feature["street_address3"]]
        )
        # Opening hours could be added
        yield item
