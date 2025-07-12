import json

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class CircleKIrelandSpider(JSONBlobSpider):
    name = "circle_k_ireland"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.ie/station-search"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        return json.loads(
            response.xpath('//script[@type="application/json"]/text()')
            .get()
            .replace("\/sites\/{siteId}\/", "")
            .replace("\/sites\/{siteId}", "details")
        )["ck_sim_search"]["station_results"]

    def post_process_item(self, item, response, location):
        apply_category(Categories.FUEL_STATION, item)
        item["name"] = location["details"]["name"]
        item["ref"] = location["details"]["id"]
        if item["name"].startswith("CIRCLE K EXPRESS "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K EXPRESS ")
            item["name"] = "Circle K Express"
        elif item["name"].startswith("CIRCLEK EXPRESS "):
            item["branch"] = item.pop("name").removeprefix("CIRCLEK EXPRESS")
        elif item["name"].startswith("CIRCLE K "):
            item["branch"] = item.pop("name").removeprefix("CIRCLE K ")
        yield item

    def pre_process_data(self, feature):
        feature["address"] = feature["addresses"]["PHYSICAL"]
        feature.pop("addresses")
