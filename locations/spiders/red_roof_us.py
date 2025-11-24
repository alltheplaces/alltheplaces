import re
from datetime import datetime
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Drink, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.react_server_components import parse_rsc

BRANDS = {
    "RRI": {"brand": "Red Roof Inn", "brand_wikidata": "Q7304949"},
    "RRIPLUS": {"brand": "Red Roof PLUS+"},
    "REDCOLLECT": {"brand": "Red Collection"},
    "HTS": {"brand": "HomeTowne Studios", "brand_wikidata": "Q109868848"},
}


def get_time_from_iso(s):
    if s:
        return datetime.fromisoformat(s).strftime("%H:%M")
    else:
        return None


class RedRoofUSSpider(SitemapSpider):
    name = "red_roof_us"
    item_attributes = {"brand_wikidata": "Q7304949"}
    sitemap_urls = ["https://www.redroof.com/sitemap.xml"]
    sitemap_rules = [(r"^https://www.redroof.com/[\w/]*property/\w{2}/[\w-]+/(\w+)", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        data = dict(parse_rsc(rsc))

        pms_data = DictParser.get_nested_key(data, "pmsData")
        item = DictParser.parse(pms_data)
        item.update(BRANDS.get(pms_data["brand"], {}))
        item["extras"]["check_in"] = get_time_from_iso(pms_data["checkInTime"])
        item["extras"]["check_out"] = get_time_from_iso(pms_data["checkOutTime"])
        item["name"] = pms_data["description"]
        item["addr_full"] = pms_data["displayAddressWithZip"]
        item["extras"]["fax"] = pms_data["faxNumber"]
        item["ref"] = pms_data["propertyId"]
        item["street_address"] = pms_data["street1"]
        if pms_data["propertyName"] != pms_data["description"]:
            item["branch"] = pms_data["propertyName"]

        item["website"] = response.url
        if not item["ref"]:
            for rule in self.sitemap_rules:
                if match := re.search(rule[0], response.url):
                    if len(match.groups()) > 0:
                        item["ref"] = match.group(1).upper()

        cms_data = DictParser.get_nested_key(data, "cmsData")["componentContent"]
        item["image"] = cms_data["propertyImage"]["image"]["originalUrl"]
        del cms_data["roomDetails"]
        amenities = set(DictParser.iter_matching_keys(cms_data, "key"))
        apply_yes_no(Extras.WHEELCHAIR, item, "AdaAccessibleRooms" in amenities)
        apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "AccessiblePublicRestrooms" in amenities)
        apply_yes_no(Extras.ATM, item, "Atm" in amenities)
        apply_yes_no(Extras.SWIMMING_POOL, item, "IndoorPool" in amenities or "Pool" in amenities)
        apply_yes_no(Extras.PICNIC_TABLES, item, "PicnicArea" in amenities)
        apply_yes_no(Drink.COFFEE, item, "FreeCoffeeLobby" in amenities)
        apply_yes_no(
            Extras.BREAKFAST,
            item,
            not amenities.isdisjoint({"FreeHotBreakfast", "FreeContinentalBreakfast", "FreeGrabGoBreakfast"}),
        )
        apply_yes_no(Extras.WIFI, item, "FreeWifi" in amenities or "VerifiedWifi" in amenities)
        apply_yes_no(
            Extras.PETS_ALLOWED,
            item,
            not amenities.isdisjoint({"PetsOnly1Allowed", "PetsUpto2Allowed", "PetsUpto3Allowed", "PetsUpto4Allowed"}),
            "PetsNotAllowed" not in amenities,
        )
        if "SmokeFree" in amenities:
            apply_yes_no(Extras.SMOKING, item, False, False)

        yield item
