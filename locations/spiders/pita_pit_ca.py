import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PitaPitCASpider(SitemapSpider):
    name = "pita_pit_ca"
    item_attributes = {"brand": "Pita Pit", "brand_wikidata": "Q7757289"}
    sitemap_urls = ["https://pitapit.ca/robots.txt"]
    sitemap_follow = ["restaurants"]
    sitemap_rules = [(r"^https://pitapit.ca/restaurants/([^/]+)/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = response.xpath("//h1//text()").get("").removeprefix("Pita Pit").strip()
        item["addr_full"] = merge_address_lines(
            response.xpath('//div[contains(concat(" ", @class, " "), " fusion-text-1 ")]//text()').getall()
        )
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').get("").removeprefix("tel:") or None

        maps_link = response.xpath('//a[contains(@href, "/maps")]/@href').get("")
        if coords := re.search(r"!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)", maps_link):
            item["lon"], item["lat"] = coords.groups()
        elif coords := re.search(r"/@(-?\d+\.\d+),(-?\d+\.\d+)", maps_link):
            item["lat"], item["lon"] = coords.groups()

        item["extras"]["website:en"] = response.url
        item["extras"]["website:fr"] = response.xpath('//a[@title="Switch to FR"]/@href').get()

        item["opening_hours"] = self.parse_hours(response)
        apply_category(Categories.FAST_FOOD, item)

        yield item

    def parse_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for row in response.xpath('//div[contains(@class, "fusion-builder-row-inner")]'):
            day = row.xpath('.//div[contains(@class, "fusion_builder_column_inner_1_3")]//text()').get("").strip()
            if sanitise_day(day, DAYS_EN) is None:
                continue
            times = " ".join(
                t.strip()
                for t in row.xpath('.//div[contains(@class, "fusion_builder_column_inner_2_3")]//text()').getall()
                if t.strip()
            )
            if not times:
                continue
            oh.add_ranges_from_string(f"{day} {times}")
        return oh
