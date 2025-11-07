import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class VolvoSpider(scrapy.Spider):
    name = "volvo"
    item_attributes = {"brand": "Volvo", "brand_wikidata": "Q215293"}
    allowed_domains = ["volvocars.com"]
    start_urls = [
        "https://www.volvocars.com/fr/dealers/concessionnaire",
        "https://www.volvocars.com/fr-be/dealers/distributeurs",
        "https://www.volvocars.com/de/dealers/haendlersuche",
        "https://www.volvocars.com/es/dealers/concesionarios-talleres",
        "https://www.volvocars.com/it/dealers/concessionari",
        "https://www.volvocars.com/uk/dealers/car-retailers",
        "https://www.volvocars.com/nl/dealers/autodealers",
    ]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        country = re.search(r"(\w\w)/dealers", response.url).group(1)
        raw_data = json.loads(
            re.search(
                r"retailers\":(\[.*\]),\"preview",
                response.xpath('//*[contains(text(),"latitude")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for location in raw_data:
            item = DictParser.parse(location)
            item["ref"] = location.get("partnerId")
            item["country"] = location.get("country") or country
            item["email"] = location.get("generalContactEmail")
            item["phone"] = location.get("phoneNumbers").get("main")

            services = location.get("capabilities") or []
            if "sales" in services:
                sales_item = item.deepcopy()
                sales_item["ref"] = sales_item["ref"] + "-SALES"
                if hours_data := location["openingHours"]["retailer"]:
                    sales_item["opening_hours"] = self.parse_opening_hours(hours_data)
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item
            elif "service" in services:
                service_item = item.deepcopy()
                service_item["ref"] = service_item["ref"] + "-SERVICE"
                if hours_data := location["openingHours"]["service"]:
                    sales_item["opening_hours"] = self.parse_opening_hours(hours_data)
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item

    def parse_opening_hours(self, hours_data: dict):
        oh = OpeningHours()
        for day, times in hours_data.items():
            day = sanitise_day(day)
            if day and times:
                for time in times:
                    oh.add_range(day, time.get("start"), time.get("end"))
        return oh
