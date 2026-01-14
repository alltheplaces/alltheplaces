import html
from typing import Any

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import Categories, McdonaldsSpider


class McdonaldsMTSpider(Spider):
    name = "mcdonalds_mt"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.com.mt/locate/"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield FormRequest(
            url="https://mcdonalds.com.mt/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_locations",
                "token": response.xpath('//script[@id="locate-js-extra"]/text()').re_first('"ajax_nonce":"(.+?)",'),
            },
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location.update(location.pop("latlng"))
            location.pop("street_number", "")  # street address data not consistent,
            location.pop("street_name", "")  # addr_full gets populated with proper address
            item = DictParser.parse(location)
            item["branch"] = html.unescape(item.pop("name"))
            item["website"] = location["permalink"]
            if services := location.get("terms"):
                apply_yes_no(Extras.DELIVERY, item, "mcdelivery" in services)
                apply_yes_no(Extras.OUTDOOR_SEATING, item, "outdoor-seating" in services)
                apply_yes_no(Extras.DRIVE_THROUGH, item, "drive-thru" in services)
                apply_yes_no(Extras.SELF_CHECKOUT, item, "self-ordering-kiosk" in services)
                apply_yes_no(Extras.WHEELCHAIR, item, "wheel-chair-accessibility" in services)

            if "mccafe" in location["terms"]:
                mccafe = item.deepcopy()
                mccafe["ref"] = "{}-mccafe".format(item["ref"])
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                yield mccafe

            yield item
