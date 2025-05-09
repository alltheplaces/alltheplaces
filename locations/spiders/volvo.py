import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines
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
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response):
        country = re.search(r"(\w\w)/dealers", response.url).group(1)

        data_raw = response.xpath('//script[@id="__NEXT_DATA__" and @type="application/json"]/text()').get()
        locator = json.loads(data_raw)["props"]["pageProps"]["retailers"]
        for row in locator:
            row["address"] = merge_address_lines([row.pop("addressLine1", ""), row.pop("addressLine2", "")])
            item = DictParser.parse(row)
            item["ref"] = row.get("partnerId")
            item["country"] = row.get("country") or country
            item["phone"] = row.get("phoneNumbers", {}).get("retailer")
            item["email"] = row.get("generalContactEmail")

            if opening_hours := row.get("openingHours"):
                item["opening_hours"] = OpeningHours()
                for day, times in opening_hours.items():
                    day = sanitise_day(day)
                    if not day:
                        continue
                    for time in times:
                        item["opening_hours"].add_range(day, time["start"], time["end"])

            apply_category(Categories.SHOP_CAR, item)

            yield item
