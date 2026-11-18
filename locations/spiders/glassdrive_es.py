from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GlassdriveESSpider(SitemapSpider, StructuredDataSpider):
    name = "glassdrive_es"
    item_attributes = {"brand": "Glassdrive", "brand_wikidata": "Q127276785"}
    sitemap_urls = ["https://locator.glassdrive.es/robots.txt"]
    sitemap_rules = [(r"\.es/[^/]+/[^/]+/[^/]+/glassdrive-[^/]+$", "parse")]
    wanted_types = ["AutoRepair"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Glassdrive ")
        item["opening_hours"] = self.parse_opening_hours(response)
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item

    def parse_opening_hours(self, response: TextResponse, **kwargs) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('//div[@class="daylist"]//tbody/tr'):
            day = sanitise_day(rule.xpath('.//span[@class="span-dayname"]/text()').get(), DAYS_ES)
            if rule.xpath('./td/span[contains(text(), "Cerrado")]'):
                oh.set_closed(day)
            else:
                for times in rule.xpath('.//div[@class="time-open"]'):
                    oh.add_range(
                        day,
                        times.xpath('./span[@class="timeContent"][1]/text()').get(),
                        times.xpath('./span[@class="timeContent"][2]/text()').get(),
                    )
        return oh
