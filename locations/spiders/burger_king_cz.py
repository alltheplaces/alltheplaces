from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCZSpider(Spider):
    name = "burger_king_cz"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    allowed_domains = ["burgerking.cz"]
    start_urls = ["https://burgerking.cz/restaurants"]
    prefixes = ["Burger King", "BurgerKing", "BK"]

    def parse(self, response):
        next_build_manifest = response.xpath('//script[contains(@src, "/_buildManifest.js")]/@src').get()
        next_build_id = next_build_manifest.replace("/_next/static/", "").replace("/_buildManifest.js", "")
        yield JsonRequest(
            url=f"https://burgerking.cz/_next/data/{next_build_id}/restaurants.json", callback=self.parse_locations
        )

    def parse_locations(self, response):
        for ref, location in response.json()["pageProps"]["initialState"]["restaurant"]["restaurants"].items():
            if not location["active"] or location["tempDisabled"]:
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            for prefix in self.prefixes:
                item["branch"] = item["branch"].removeprefix(prefix)
            item["branch"] = item["branch"].strip()
            item["housenumber"] = location["address"]["number"]
            slug = unidecode(location["name"]).lower().replace(" ", "-")
            item["website"] = item["extras"]["website:cs"] = urljoin("https://burgerking.cz/restaurants/", slug)
            item["extras"]["website:en"] = urljoin("https://burgerking.cz/en/restaurants/", slug)

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name, day_hours in location["weeklyWorkingHours"].items():
                for time_period in day_hours:
                    time_from = time_period["from"]
                    time_to = time_period["to"]
                    hours_string = f"{hours_string} {day_name}: {time_from} - {time_to}"
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
