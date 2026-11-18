import base64
import json
import re
from typing import Any, Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class DunnTireUSSpider(Spider):
    name = "dunn_tire_us"
    item_attributes = {"brand": "Dunn Tire"}
    allowed_domains = ["www.dunntire.com"]
    start_urls = ["https://www.dunntire.com/directions"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        encoded_data = response.xpath(
            '//div[@data-widget-id="eb350023d54a4f3eb64b7e040889da87"]/@data-widget-config'
        ).get()
        data = json.loads(base64.b64decode(encoded_data))

        for location in data["locationsList"]:
            website = location.get("locationWebsiteAddress")
            if not website or urlparse(website).hostname != "www.dunntire.com":
                continue

            item = Feature()
            item["ref"] = urlparse(website).path.strip("/").lower()
            item["branch"] = location.get("locationName")
            item["addr_full"] = (location.get("locationAddress") or "").strip(" ,")
            item["lat"] = location.get("locationLat")
            item["lon"] = location.get("locationLng")
            item["phone"] = location.get("locationPhone")
            item["website"] = website
            item["image"] = location.get("locationImage")

            hours_string = re.sub(r"<br\s*/?>", " ", location.get("locationShopHours") or "", flags=re.I)
            hours = OpeningHours()
            hours.add_ranges_from_string(hours_string)
            item["opening_hours"] = hours

            apply_category(Categories.SHOP_TYRES, item)
            yield item
