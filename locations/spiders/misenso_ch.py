import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MisensoCHSpider(Spider):
    name = "misenso_ch"
    item_attributes = {"name": "Misenso", "brand": "Misenso", "brand_wikidata": "Q116151325"}
    start_urls = ["https://www.misenso.ch/de/filialen/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//@data-stores").get()):
            data = json.loads(location["google_place_data"])
            item = Feature()
            item["ref"] = str(location["id"])
            item["lat"] = data["location"]["lat"]
            item["lon"] = data["location"]["lng"]
            item["branch"] = location["title"].removeprefix("Misenso ")

            item["website"] = item["extras"]["website:de"] = location["page_link_de"]
            item["extras"]["website:fr"] = location["page_link_fr"]
            item["extras"]["ref:google"] = location["place_id"]

            item["opening_hours"] = OpeningHours()
            for day, times in location["amparex"]["opening_hours"].items():
                item["opening_hours"].add_range(day, times["from"], times["to"])

            apply_category(Categories.SHOP_OPTICIAN, item)

            yield item
