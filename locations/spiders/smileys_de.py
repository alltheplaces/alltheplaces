from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class SmileysDESpider(Spider):
    name = "smileys_de"
    item_attributes = {"brand": "Smiley's", "brand_wikidata": "Q60998945"}
    start_urls = ["https://shop.smileys.de/api/v1/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["stores"]:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["address"]["lat"]
            item["lon"] = location["address"]["lng"]
            item["branch"] = location["name"]
            item["housenumber"] = location["address"]["number"]
            item["street"] = location["address"]["street"]
            item["city"] = location["address"]["city"]
            item["state"] = location["address"]["state"]
            item["postcode"] = location["address"]["zipcode"]
            item["website"] = urljoin("https://www.smileys.de/bestellen/", location["url_name"])  # bad data
            item["phone"] = location["address"]["phone"]
            item["extras"]["fax"] = location["address"].get("fax")

            apply_yes_no(Extras.TAKEAWAY, item, location["modes"]["pickup"])
            apply_yes_no(Extras.DELIVERY, item, location["modes"]["delivery"])

            apply_category(Categories.FAST_FOOD, item)

            yield item
