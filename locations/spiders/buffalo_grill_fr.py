import re
from typing import ClassVar, Iterable

from scrapy import FormRequest
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BuffaloGrillFRSpider(SitemapSpider, StructuredDataSpider):
    name = "buffalo_grill_fr"
    item_attributes: ClassVar[dict[str, str]] = {"brand": "Buffalo Grill", "brand_wikidata": "Q944655"}
    sitemap_urls: ClassVar[list[str]] = ["https://www.buffalo-grill.fr/sitemap.xml"]
    sitemap_rules: ClassVar[list[tuple[str, str]]] = [(r"/nos-restaurants/([^/]+)/?$", "parse")]
    wanted_types: ClassVar[list[str]] = ["Restaurant"]

    def parse(self, response: TextResponse, **kwargs):
        if not (restaurant_id := response.css(".restaurant_full::attr(data-restaurant)").get()):
            yield from self.parse_sd(response)
            return

        yield FormRequest(
            "https://www.buffalo-grill.fr/ajax/restaurant/schedules",
            formdata={"restaurantId": restaurant_id, "type": "schedules_full"},
            callback=self.parse_schedules,
            errback=self.parse_schedules_error,
            cb_kwargs={"location_response": response},
        )

    def parse_schedules(self, response: TextResponse, location_response: TextResponse):
        body = location_response.body.replace(b"</body>", response.body + b"</body>")
        yield from self.parse_sd(location_response.replace(body=body))

    def parse_schedules_error(self, failure):
        yield from self.parse_sd(failure.request.cb_kwargs["location_response"])

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if item["country"] == "FRA":
            item["country"] = "FR"
        elif item["country"] != "FR":
            return

        item["branch"] = item.pop("name")
        item["opening_hours"] = self.parse_opening_hours(response)
        item["website"] = response.url
        item["extras"]["@source_uri"] = response.url

        apply_category(Categories.RESTAURANT, item)
        yield item

    @staticmethod
    def parse_opening_hours(response: TextResponse) -> OpeningHours:
        opening_hours = OpeningHours()
        for element in response.css(".fiche-restaurant-hourly-item"):
            text = " ".join(" ".join(element.xpath(".//text()").getall()).split())
            day_text, _, hours_text = text.partition(" ")
            if not (day := sanitise_day(day_text, DAYS_FR)):
                continue
            if "ferm" in hours_text.lower():
                opening_hours.set_closed(day)
                continue
            for open_time, close_time in re.findall(r"(\d{1,2}:\d{2})\s+à\s+(\d{1,2}:\d{2})", hours_text):
                opening_hours.add_range(day, open_time, close_time)
        return opening_hours
