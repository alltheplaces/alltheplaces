from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LeonidasSpider(JSONBlobSpider):
    name = "leonidas"
    item_attributes = {"brand": "Leonidas", "brand_wikidata": "Q80335"}
    start_urls = ["https://my-leonidas.com/api/public/store-locator"]
    locations_key = "shops"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name").upper().removeprefix("LEONIDAS ")
        for lang, url in feature["official_page_urls"].items():
            item["extras"]["website:{}".format(lang)] = url
        item["website"] = item["extras"]["website:fr"] if item["country"] == "FR" else item["extras"]["website:en"]
        try:
            oh = OpeningHours()
            for day, times in (feature.get("opening_hours") or {}).items():
                for time in times or []:
                    oh.add_range(day, time["opens"], time["closes"])
            item["opening_hours"] = oh
        except:
            pass

        apply_category(Categories.SHOP_CHOCOLATE, item)
        yield item
