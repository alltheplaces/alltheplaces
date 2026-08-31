import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

HOUR_RANGE = re.compile(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*[-–]\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", re.IGNORECASE)


class SquiresLoftAUSpider(SitemapSpider):
    name = "squires_loft_au"
    item_attributes = {"brand": "Squires Loft", "brand_wikidata": "Q141237587", "name": "Squires Loft"}
    sitemap_urls = ["https://squiresloft.com.au/our-locations-sitemap.xml"]
    sitemap_rules = [(r"/our-locations/[^/]+/$", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = response.url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title()

        item["addr_full"] = response.xpath('//div[@class="cntbox loc_add"]//a/text()').get()
        item["phone"] = response.xpath('//div[@class="cntbox lcon_num"]//a/text()').get()
        item["email"] = response.xpath('//div[@class="cntbox lemail_add"]//a/text()').get()

        if map_url := response.xpath('//iframe[contains(@data-src, "maps/embed")]/@data-src').get():
            item["lat"], item["lon"] = url_to_coords(map_url)

        item["opening_hours"] = self.parse_hours(response)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"

        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            text = (
                response.xpath(f'//div[@class="timeslot"][starts-with(normalize-space(.), "{day}:")]')
                .xpath("string(.)")
                .get()
            )
            if not text:
                continue
            text = text.split(":", 1)[1]
            if "closed" in text.lower():
                oh.set_closed(day)
                continue
            for open_time, close_time in HOUR_RANGE.findall(text):
                oh.add_range(
                    day,
                    self.normalise_time(open_time),
                    self.normalise_time(close_time),
                    time_format="%I:%M%p",
                )
        return oh

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.strip().lower().replace(" ", "")
        if ":" not in value:
            value = value.replace("am", ":00am").replace("pm", ":00pm")
        return value
