import html

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsMTSpider(scrapy.Spider):
    name = "mcdonalds_mt"
    item_attributes = McDonaldsSpider.item_attributes
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        form_data = {"action": "get_locations", "token": "5c4d2f74ce"}
        yield scrapy.http.FormRequest(
            url="https://mcdonalds.com.mt/wp-admin/admin-ajax.php",
            formdata=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
            callback=self.parse,
        )

    def parse(self, response):
        for location in response.json()["data"]:
            location.update(location.pop("latlng"))
            location.pop("street_number", "")  # street address data not consistent,
            location.pop("street_name", "")  # addr_full gets populated with proper address
            item = DictParser.parse(location)
            item["name"] = html.unescape(location.get("title"))
            if services := location.get("terms"):
                apply_yes_no(Extras.DELIVERY, item, "mcdelivery" in services)
                apply_yes_no(Extras.OUTDOOR_SEATING, item, "outdoor-seating" in services)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "drive-thru" in services)
                apply_yes_no(Extras.SELF_CHECKOUT, item, "self-ordering-kiosk" in services)
                apply_yes_no(Extras.WHEELCHAIR, item, "wheel-chair-accessibility" in services)
            yield item
