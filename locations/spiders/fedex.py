import re
from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import ITEM_PIPELINES


class FedexSpider(CrawlSpider):
    name = "fedex"
    item_attributes = {"brand": "FedEx", "brand_wikidata": "Q459477"}
    CATEGORY_MAP = {
        "FedEx Air Freight Center": None,
        "FedEx Drop Box": Categories.POST_BOX,
        "FedEx Express Drop Box": Categories.POST_BOX,
        "FedEx ShipSite": Categories.POST_OFFICE,
        "FedEx Self-Service Locker": Categories.PARCEL_LOCKER,
        "FedEx Office Print & Ship Center": Categories.SHOP_COPYSHOP,
        "FedEx Station": Categories.POST_DEPOT,
        "FedEx OnSite": Categories.POST_PARTNER,
        "Centro de Envío FedEx": Categories.POST_OFFICE,
        "FedEx Ship Center": Categories.POST_OFFICE,
        "FedEx Authorized ShipCenter": Categories.POST_PARTNER,
        "FedEx Office Ship Center": Categories.POST_OFFICE,
        "FedEx World Service Center": Categories.POST_OFFICE,
    }
    custom_settings = {  # Disable NSI matching
        "ITEM_PIPELINES": ITEM_PIPELINES
        | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None},
    }
    start_urls = ["https://local.fedex.com/en"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"en-[a-z]{2}$", restrict_xpaths='//*[@class="Directory-listLinks Directory-countrySection"]'
            ),
            callback="parse",
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        country = response.url.strip("/").split("-")[-1].upper().replace("GB", "UK")
        if country in ["US"]:  # Contains the majority of locations, so we'll make request city wise to get max count
            for city in city_locations(country, 10000):
                yield JsonRequest(
                    url=f'https://local.fedex.com/en/search?q={city["name"], country}&r=50&per=50',
                    callback=self.parse_locations,
                )
        else:
            locations_list = response.xpath('//*[@class="Directory-listLinkText"]/text()').getall()
            for location in locations_list:
                yield JsonRequest(
                    url=f"https://local.fedex.com/en/search?q={location, country}&r=50&per=50",
                    callback=self.parse_locations,
                )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("response", {}).get("entities", []):
            location_info = location.get("profile")
            if coordinates := location_info.get("geocodedCoordinate") or location_info.get("displayCoordinate"):
                location_info.update(coordinates)
            location_info.update(location_info.pop("meta"))
            item = DictParser.parse(location_info)
            item["street_address"] = merge_address_lines(
                [
                    location_info["address"]["line1"],
                    location_info["address"]["line2"],
                    location_info["address"]["line3"],
                ]
            )
            item["phone"] = location_info.get("mainPhone", {}).get("number")
            item["phone"] = "; ".join(
                filter(
                    None,
                    [
                        location_info.get("mainPhone", {}).get("number"),
                        location_info.get("mobilePhone", {}).get("number"),
                    ],
                )
            )
            item["extras"]["fax"] = location_info.get("fax", {}).get("number")
            item["name"] = item["name"].split("(Permit to Enter)")[0].strip().replace("Centre", "Center")
            if "FedEx Express" in item["name"]:
                item["brand"] = "FedEx Express"
            if category := self.CATEGORY_MAP.get(item["name"]):
                apply_category(category, item)

            item["opening_hours"] = OpeningHours()
            for rule in location_info.get("hours", {}).get("normalHours", []):
                if day := sanitise_day(rule.get("day")):
                    if rule.get("isClosed"):
                        item["opening_hours"].set_closed(day)
                    else:
                        for shift in rule.get("intervals", []):
                            if shift.get("start") and shift.get("end"):
                                open_time = self.clean_hours(str(shift["start"]))
                                close_time = self.clean_hours(str(shift["end"]))
                                item["opening_hours"].add_range(day, open_time, close_time)

            yield item

    def clean_hours(self, hours: str) -> str:
        if not hours:
            return ""
        hours = hours.zfill(4) if ":" not in hours else hours.zfill(5)
        hours = re.sub(r"(\d{2})(\d{2})", r"\1:\2", hours)
        return hours
