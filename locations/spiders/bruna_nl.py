import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.json_blob_spider import JSONBlobSpider


class BrunaNLSpider(JSONBlobSpider):
    name = "bruna_nl"
    item_attributes = {"brand": "Bruna", "brand_wikidata": "Q3317555"}
    start_urls = ["https://www.bruna.nl/INTERSHOP/rest/WFS/tba-bruna_nl-Site/-/stores"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("attributes"))
        feature["street-address"] = feature.pop("address")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Bruna - ")
        item["phone"] = feature.get("phoneBusiness")
        set_social_media(item, SocialMedia.WHATSAPP, feature.get("whatsapp"))
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if hours := feature.get(f"open{day}"):
                for open_time, close_time in re.findall(r"(\d+:\d+)[-\s]+(\d+:\d+)", hours.replace(".", ":")):
                    item["opening_hours"].add_range(day, open_time, close_time)
        item["website"] = f'https://www.bruna.nl/winkels/{item["city"].lower().replace(" ", "-")}/{item["ref"]}'
        apply_category(Categories.SHOP_BOOKS, item)
        yield item
