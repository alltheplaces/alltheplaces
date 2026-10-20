from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class FamilyExpressUSSpider(Spider):
    name = "family_express_us"
    item_attributes = {"brand": "Family Express", "brand_wikidata": "Q85760458"}
    allowed_domains = ["www.familyexpress.com"]
    start_urls = ["https://www.familyexpress.com/api/locations/place"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for place in response.json()["places"]:
            location = place.get("yextData")
            if not location or location.get("meta", {}).get("entityType") != "location":
                continue
            # Some entities at this API are FAQ articles, the corporate
            # headquarters/distribution centre, or unrelated co-located
            # tenants rather than retail stores; only "Convenience Store" is
            # tagged consistently across every actual retail location.
            if "Convenience Store" not in (location.get("keywords") or []):
                continue

            item = DictParser.parse(location)
            item["ref"] = str(place["storeId"])
            item["branch"] = location.get("c_subName")
            if website_url := location.get("websiteUrl"):
                item["website"] = website_url.get("url")
            if hours := location.get("hours"):
                item["opening_hours"] = YextSpider.parse_opening_hours(hours)

            apply_category(Categories.SHOP_CONVENIENCE, item)
            if place.get("products"):
                apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.CAR_WASH, item, location.get("c_carWash") is True)
            apply_yes_no(Extras.ATM, item, "ATM" in (location.get("keywords") or []))

            yield item
