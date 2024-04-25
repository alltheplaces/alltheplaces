import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class PennyDESpider(scrapy.Spider):
    name = "penny_de"
    item_attributes = {"brand_wikidata": "Q284688"}
    allowed_domains = ["penny.de"]
    start_urls = ("https://www.penny.de/.rest/market",)

    @staticmethod
    def parse_hours(location: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS_FULL:
            if location.get(f"closed{day}"):
                continue
            opening_hours.add_range(day, location[f"opensAt{day}"], location[f"closesAt{day}"])

        return opening_hours

    def parse(self, response, **kwargs):
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = location["marketName"].removeprefix("Penny ")
            item["street_address"] = location["streetWithHouseNumber"]
            item["website"] = response.urljoin(
                "/".join(["/markt", location["citySlug"], location["wwIdent"], location["slug"]])
            )
            item["image"] = location["image"]
            item["ref"] = location["@id"]
            item["opening_hours"] = self.parse_hours(location)

            yield item
