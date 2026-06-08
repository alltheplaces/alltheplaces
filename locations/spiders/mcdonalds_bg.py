import re
from typing import Any
from urllib.parse import unquote

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsBGSpider(Spider):
    name = "mcdonalds_bg"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.bg"]
    start_urls = ["https://mcdonalds.bg/en/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        ajax_endpoints = re.search(
            r"get_filtered_posts\":\"(.+)\",\"get_restaurant",
            unquote(response.xpath('//*[@id="wgs-endpoints-js-extra"]/@src').get()),
        ).group(1)
        ajax_action = "get_filtered_posts"
        yield FormRequest(
            url="https://mcdonalds.bg/wp-admin/admin-ajax.php",
            formdata={"action": ajax_action, "ajax-nonce": ajax_endpoints},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location.update(location.pop("address_on_map", {}))
            item = DictParser.parse(location)
            item["ref"] = str(item["ref"])
            if isinstance(location.get("city"), dict):
                item["city"] = location["city"].get("city_name")
            if phone_numbers := location.get("phone_numbers", []):
                item["phone"] = phone_numbers[0]
            item["website"] = None

            services = [benefit.get("name") for benefit in location.get("benefits", [])]
            if "McCafe™" in services:
                mccafe = item.deepcopy()
                mccafe["ref"] += "_mccafe"
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                yield mccafe
            apply_yes_no(Extras.WIFI, item, "WiFi" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "McDrive™" in services)

            apply_yes_no(Extras.DELIVERY, item, location.get("is_delivery_available"))

            yield item
