import html
from typing import Any, Iterable

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.mcdonalds import Categories, McdonaldsSpider


class McdonaldsPremierCapitalSpider(Spider):
    """
    Premier Capital is the operator of McDonald's in EE, GR, LT, LV, MT and RO. This class contains the common spider
    code for their store finders.
    """

    item_attributes = McdonaldsSpider.item_attributes
    domain: str
    requires_proxy = True
    services = {
        "bezmaksas-wifi": Extras.WIFI,
        "brokastis-no-6-lidz-10%e2%80%8b": Extras.BREAKFAST,
        "drive-thru": Extras.DRIVE_THROUGH,
        "elektromobilio-ikroviklis": "charging_station",
        "freewifi": Extras.WIFI,
        "hommikusook-kell-600-1000": Extras.BREAKFAST,
        "iseteeninduskioskid": Extras.SELF_CHECKOUT,
        "mcdelivery": Extras.DELIVERY,
        "mcdrive-24h": Extras.DRIVE_THROUGH,
        "mcexpress": "McExpress",
        "mobile-order-and-pay": "payment:mobile_app",
        "nemokamas-wifi-interneto-rysys": Extras.WIFI,
        "outdoor-seating": Extras.OUTDOOR_SEATING,
        "pasapkalposanas-kiosks": Extras.SELF_CHECKOUT,
        "pusryciai-nuo-6-00-iki-10-00-val": Extras.BREAKFAST,
        "savitarnos-kioskas": Extras.SELF_CHECKOUT,
        "self-ordering-kiosk": Extras.SELF_CHECKOUT,
        "tasuta-wi-fi": Extras.WIFI,
        "walk-thru": "walk_thru",
        "wheel-chair-accessibility": Extras.WHEELCHAIR,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield FormRequest(
            url=f"https://{self.domain}/wp-admin/admin-ajax.php",
            formdata={
                "action": "get_locations",
                "token": response.xpath('//script[@id="locate-js-extra"]/text()').re_first('"ajax_nonce":"(.+?)",'),
            },
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["data"]:
            location.update(location.pop("latlng"))
            location.pop("street_number", "")  # street address data not consistent,
            location.pop("street_name", "")  # addr_full gets populated with proper address
            item = DictParser.parse(location)
            item["branch"] = html.unescape(item.pop("name"))
            item["website"] = location["permalink"]
            if services := location.get("terms"):
                for key, extra in self.services.items():
                    apply_yes_no(extra, item, key in services)

            if "mccafe" in location["terms"]:
                mccafe = item.deepcopy()
                mccafe["ref"] = "{}-mccafe".format(item["ref"])
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                yield mccafe

            yield item
