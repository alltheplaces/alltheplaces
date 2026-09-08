import re
from typing import Iterable

from scrapy import FormRequest
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BuffaloGrillFRSpider(SitemapSpider, StructuredDataSpider):
    name = "buffalo_grill_fr"
    item_attributes = {"brand": "Buffalo Grill", "brand_wikidata": "Q944655"}
    sitemap_urls = ["https://www.buffalo-grill.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/([^/]+)/?$", "parse")]
    wanted_types = ["Restaurant"]

    def parse(self, response: TextResponse, **kwargs):
        yield FormRequest(
            "https://www.buffalo-grill.fr/ajax/restaurant/schedules",
            formdata={"restaurantId": response.xpath("//@data-restaurant").get(), "type": "schedules_full"},
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
