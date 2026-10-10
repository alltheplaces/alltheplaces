import re
from typing import Any, Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BOT_USER_AGENT_SCRAPY


class HallensteinBrothersAUNZSpider(JSONBlobSpider):
    name = "hallenstein_brothers_au_nz"
    item_attributes = {"brand": "Hallenstein Brothers", "brand_wikidata": "Q24189399"}
    allowed_domains = ["www.hallensteins.com"]
    start_urls = ["https://www.hallensteins.com/store-locations/all-stores-worldwide"]
    custom_settings = {"USER_AGENT": BOT_USER_AGENT_SCRAPY}

    def extract_json(self, response):
        js_blob = (
            response.xpath('//script[contains(text(), "var ga_stores = ")]/text()')
            .get()
            .split("var ga_stores = ", 1)[1]
            .split("; // all store data", 1)[0]
        )
        return parse_js_object(js_blob)

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        if "closed permanently" in (feature.get("openinghours") or "").lower():
            return
        item["branch"] = item.pop("name", None)
        if feature.get("locale") == "NZ":
            item.pop("state", None)

        state_urlsafe = re.sub(r"\s+", "-", feature["region"].lower().strip())
        name_urlsafe = re.sub(r"\s+", "-", feature["name"].lower().strip())
        item["website"] = "https://www.hallensteins.com/store-locations/{}/{}".format(state_urlsafe, name_urlsafe)

        if hours := feature.get("openinghours"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)

        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes([Clothes.MEN], item)

        yield item
