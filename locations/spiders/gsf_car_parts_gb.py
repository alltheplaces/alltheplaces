import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GsfCarPartsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "gsf_car_parts_gb"
    item_attributes = {"brand": "GSF Car Parts", "brand_wikidata": "Q80963064"}
    sitemap_urls = ["https://www.gsfcarparts.com/robots.txt"]
    sitemap_follow = ["branch-sitemap"]
    sitemap_rules = [(r"/branches/([-\w]+)$", "parse")]
    wanted_types = ["Organization"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("GSF Car Parts - ")
        item["city"] = item.pop("state")
        item["facebook"] = None

        item["opening_hours"] = self.parse_opening_hours(response)

        if m := re.search(r"\\\"center\\\":\{\\\"lat\\\":(-?\d+\.\d+),\\\"lng\\\":(-?\d+\.\d+)}", response.text):
            item["lat"], item["lon"] = m.groups()

        apply_category(Categories.SHOP_CAR_PARTS, item)

        yield item

    def parse_opening_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('//div[@class="store-timings"]/ul/li'):
            day = rule.xpath('./span[@class="day"]/text()').get()
            if rule.xpath('./span[contains(@class, "timings")][contains(text(), "Closed")]'):
                oh.set_closed(day)
            else:
                oh.add_range(
                    day,
                    rule.xpath('./div[contains(@class, "timings")]/span[1]/text()').get(),
                    rule.xpath('./div[contains(@class, "timings")]/span[2]/text()').get(),
                    time_format="%I:%M%p",
                )
        return oh
