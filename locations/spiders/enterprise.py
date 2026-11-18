from datetime import date
from typing import Any, AsyncIterator

import geonamescache
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class EnterpriseSpider(Spider):
    name = "enterprise"
    item_attributes = {"brand": "Enterprise", "brand_wikidata": "Q17085454"}
    allowed_domains = ["prd.location.enterprise.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        gc = geonamescache.GeonamesCache()
        countries = gc.get_countries()
        for country_code in countries.keys():
            yield JsonRequest(
                url=f"https://prd.location.enterprise.com/enterprise-sls/search/location/enterprise/web/country/{country_code}"
            )

    def parse(self, response):
        for location in response.json():
            if location["closed"] or not location["physicalLocation"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["stationId"]
            item["branch"] = location["locationNameTranslation"]
            item["street_address"] = clean_address(location["addressLines"])
            item["phone"] = location["formattedPhone"]
            apply_category(Categories.CAR_RENTAL, item)
            yield JsonRequest(
                url="https://prd.location.enterprise.com/enterprise-sls/search/location/enterprise/web/hours/{}?peopleSoftId={}".format(
                    location["stationId"], location["peopleSoftId"]
                ),
                cb_kwargs={"item": item},
                callback=self.parse_hours,
            )

    def parse_hours(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        oh = OpeningHours()
        seen_days = set()
        for day_date, day_data in response.json()["data"].items():
            day = DAYS[date.fromisoformat(day_date).weekday()]
            standard = day_data.get("STANDARD")
            if day in seen_days or not standard or "event" in standard:
                continue
            seen_days.add(day)
            if standard["open24Hours"]:
                oh.add_range(day, "00:00", "24:00")
            elif standard["closed"]:
                oh.set_closed(day)
            for hours in standard["hours"]:
                oh.add_range(day, hours["open"], hours["close"])
        if oh.day_hours:
            item["opening_hours"] = oh
        yield item
