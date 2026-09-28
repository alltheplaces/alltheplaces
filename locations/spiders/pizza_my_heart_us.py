import re
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class PizzaMyHeartUSSpider(StructuredDataSpider):
    name = "pizza_my_heart_us"
    item_attributes = {"brand": "Pizza My Heart", "brand_wikidata": "Q7199970"}
    allowed_domains = ["www.pizzamyheart.com"]
    start_urls = ["https://www.pizzamyheart.com/"]
    wanted_types = ["FoodEstablishment"]
    search_for_facebook = False

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for data in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if data.get("@type") == "Organization":
                yield from data.get("subOrganization") or []

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Request]:
        item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name")
        item["country"] = "US"
        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"
        yield Request(item["website"], callback=self.parse_location, meta={"item": item})

    def parse_location(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["lat"] = response.xpath('//div[contains(@class, "gmaps")]/@data-gmaps-lat').get()
        item["lon"] = response.xpath('//div[contains(@class, "gmaps")]/@data-gmaps-lng').get()
        item["facebook"] = response.xpath('//section[@id="intro"]//a[contains(@href, "facebook.com")]/@href').get()
        if not item.get("phone"):
            item["phone"] = response.xpath('//section[@id="intro"]//text()').re_first(r"\(?\d{3}\)?[ -]\d{3}-\d{4}")
        item["opening_hours"] = self.parse_opening_hours(response)
        yield item

    @staticmethod
    def parse_opening_hours(response: Response) -> OpeningHours | None:
        lines = []
        for paragraph in response.xpath('//section[@id="intro"]//p[not(.//a)]'):
            line = paragraph.xpath("normalize-space(string())").get()
            if not re.search(r"\b(?:mon|tue|wed|thu|fri|sat|sun|daily)", line, re.I):
                continue

            line = re.sub(r"\b(Fri(?:day)?)\s*&\s*(Sat(?:urday)?)\b", r"\1 - \2", line, flags=re.I)
            if match := re.fullmatch(
                r"((?:\d{1,2}(?::\d{2})?\s*[ap]m|midnight|noon))\s*-\s*"
                r"((?:\d{1,2}(?::\d{2})?\s*[ap]m|midnight|noon))\s+(.+)",
                line,
                re.I,
            ):
                line = f"{match.group(3)}: {match.group(1)} - {match.group(2)}"
            lines.append(line)

        hours = OpeningHours()
        hours.add_ranges_from_string(" ".join(lines), days=DAYS_EN)
        return hours if hours.as_opening_hours() else None
