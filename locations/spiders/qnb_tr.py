from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import set_closed


class QnbTRSpider(Spider):
    name = "qnb_tr"
    item_attributes = {"brand": "QNB", "brand_wikidata": "Q1136759"}

    async def start(self) -> AsyncIterator[Any]:
        for location_type, query in [("branch", "hasBranch=true"), ("atm", "hasAtm=true")]:
            yield JsonRequest(
                url=f"https://www.qnb.com.tr/api/City?{query}",
                cb_kwargs={"location_type": location_type},
            )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for city in response.json():
            yield JsonRequest(
                url=f"https://www.qnb.com.tr/api/{location_type}?cityId={city.get('Id')}",
                data={},
                callback=self.parse_locations,
                cb_kwargs={"location_type": location_type, "city": city.get("Name")},
            )

    def parse_locations(self, response: Response, location_type: str, city: str, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["lon"] = location.get("Longtitude")
            item["city"] = city

            if location_type == "branch":
                item["branch"] = location.get("OrganizationName")
                item["phone"] = location.get("Phone1")
                if location.get("IsTemporaryClosed"):
                    set_closed(item)
                apply_category(Categories.BANK, item)
            elif location_type == "atm":
                item["addr_full"] = location.get("Adress")
                apply_yes_no(Extras.CASH_IN, item, location.get("BuyingTL") == 1)
                apply_yes_no(Extras.CASH_OUT, item, location.get("SellingTL") == 1)
                apply_yes_no(Extras.WHEELCHAIR, item, location.get("Enable") in (1, 3))
                if location.get("IsActive") is not True:
                    set_closed(item)
                apply_category(Categories.ATM, item)
            else:
                self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item
