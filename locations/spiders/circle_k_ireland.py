import json
from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.json_blob_spider import JSONBlobSpider


class CircleKIrelandSpider(JSONBlobSpider):
    name = "circle_k_ireland"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.ie/station-search"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        return json.loads(response.xpath('//script[@type="application/json"]/text()').get().replace('\/sites\/{siteId}\/',"").replace('\/sites\/{siteId}',"details"))["ck_sim_search"]["station_results"]

#    def post_process_item(self, item, response, location):

#        yield item

    def pre_process_data(self, feature):
        feature["address"]=feature["addresses"]["PHYSICAL"]
        feature.pop("addresses")
