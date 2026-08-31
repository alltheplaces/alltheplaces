import json
from typing import Any, AsyncIterator

from scrapy.http import FormRequest, JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class GantSpider(Spider):
    name = "gant"
    item_attributes = {"brand": "GANT", "brand_wikidata": "Q1493667"}
    organization_id = "f_ecom_bfln_prd"
    site_ids = [
        "Gant-UK",
        "Gant-NORDIC",
        "Gant-DACH",
        "Gant-FR",
        "Gant-BE",
        "Gant-ES",
        "Gant-PT",
        "Gant-NL",
        "Gant-IT",
        "Gant-US",
        "Gant-CN",
    ]

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url=f"https://www.gant.co.uk/mobify/slas/private/shopper/auth/v1/organizations/{self.organization_id}/oauth2/token",
            formdata={"grant_type": "client_credentials", "channel_id": "Gant-UK"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = response.json()["access_token"]
        for site_id in self.site_ids:
            yield JsonRequest(
                url=f"https://www.gant.co.uk/mobify/proxy/api/store/shopper-stores/v1/organizations/{self.organization_id}/store-search?distanceUnit=km&latitude=48&longitude=10&maxDistance=20012&siteId={site_id}&offset=0&limit=200",
                headers={"Authorization": f"Bearer {token}"},
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("data", []):
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])
            item["branch"] = item.pop("name").removeprefix("GANT ")
            item["opening_hours"] = self.parse_hours(location.get("storeHours"))
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item

    def parse_hours(self, store_hours: str | None) -> OpeningHours:
        oh = OpeningHours()
        if not store_hours:
            return oh
        try:
            for day, rules in json.loads(store_hours).items():
                if day == "holidayHours":
                    continue
                if rules.get("isClosed"):
                    oh.set_closed(day)
                else:
                    for interval in rules.get("openIntervals", []):
                        oh.add_range(day=day, open_time=interval["start"], close_time=interval["end"])
        except (ValueError, KeyError, AttributeError):
            pass
        return oh
