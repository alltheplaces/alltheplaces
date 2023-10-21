import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, DAYS_CZ, DAYS_EN, DAYS_HU, DAYS_PL, DAYS_RO, DAYS_RS, DAYS_SK, OpeningHours


class CCCSpider(Spider):
    name = "ccc"
    item_attributes = {"brand": "CCC", "brand_wikidata": "Q11788344"}
    start_urls = [
        "https://ccc.eu/bg/sklepy",
        "https://ccc.eu/cz/sklepy",
        "https://ccc.eu/hu/sklepy",
        "https://ccc.eu/pl/sklepy",
        "https://ccc.eu/ro/sklepy",
        "https://ccc.eu/rs/sklepy",
        "https://ccc.eu/sk/sklepy",
    ]
    days_mapping = {
        "BG": DAYS_BG,
        "CZ": DAYS_CZ,
        "HU": DAYS_HU,
        "PL": DAYS_PL,
        "RO": DAYS_RO,
        "RS": DAYS_RS,
        "SK": DAYS_SK,
    }

    def parse(self, response, **kwargs):
        shop_data = response.xpath("//div[@id='pos-list-json']/text()").get()
        country = response.url.split("/")[-2].upper()
        days = DAYS_EN
        if country in self.days_mapping:
            days = self.days_mapping[country]
        for shop in json.loads(shop_data):
            item = DictParser.parse(shop)
            item["website"] = f"https://ccc.eu{shop['link']}"
            item["opening_hours"] = OpeningHours()
            item["country"] = country
            if "workingHours" in shop:
                for oh in shop["workingHours"]:
                    for hours_range, days_range in oh.items():
                        item["opening_hours"].add_ranges_from_string(f"{days_range} {hours_range}", days=days)
            yield item
