import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "mo": "Mo",
    "di": "Tu",
    "mi": "We",
    "do": "Th",
    "fr": "Fr",
    "sa": "Sa",
    "so": "Su",
}


class CommerzbankDESpider(CrawlSpider):
    name = "commerzbank_de"
    item_attributes = {"brand": "Commerzbank", "brand_wikidata": "Q157617"}
    allowed_domains = ["commerzbank.de"]
    start_urls = ["https://filialsuche.commerzbank.de/de/branch-name"]
    rules = [
        Rule(LinkExtractor(allow=r"^https://filialsuche.commerzbank.de/de/branch-name/.+$"), callback="parse_details")
    ]

    def parse_hours(self, store_info) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAY_MAPPING:
            try:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=store_info[f"{day}MorgenVon"],
                    close_time=store_info[f"{day}MorgenBis"],
                    time_format="%H:%M",
                )
            except KeyError:
                pass
        return opening_hours

    def parse_details(self, response):
        if match := re.search(
            r"var decodedResults = JSON\.parse\(\$\(\"<div\/>\"\)\.html\(\"(\[.*?\])\"",
            response.text,
        ):
            data = match.group(1)
            data = data.encode().decode("unicode-escape")
            data = json.loads(data)

            for branch in data:
                properties = {
                    "name": branch["orgTypName"],
                    "ref": branch["id"],
                    "street_address": branch["anschriftStrasse"],
                    "city": branch["anschriftOrt"],
                    "postcode": branch.get("postanschriftPostleitzahl"),
                    "country": "DE",
                    "lat": float(branch["position"][0]),
                    "lon": float(branch["position"][1]),
                    "phone": branch.get("telefon", ""),
                    "opening_hours": self.parse_hours(branch),
                    "website": response.url,
                    "extras": {
                        "fax": branch.get("telefax", ""),
                        "barriere_type": branch.get("barriereTyp", ""),
                        "cash_register": branch.get("kasse", ""),
                        "vault": branch.get("vault", ""),
                        "cashback": branch.get("cashback", ""),
                        "cashgroup": branch.get("cashgroup", ""),
                    },
                }

                apply_category(Categories.BANK, properties)

                yield Feature(**properties)
