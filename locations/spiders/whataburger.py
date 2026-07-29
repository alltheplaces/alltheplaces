from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WhataburgerSpider(SitemapSpider, StructuredDataSpider):
    name = "whataburger"
    item_attributes = {"brand": "Whataburger", "brand_wikidata": "Q376627"}
    allowed_domains = ["locations.whataburger.com"]
    sitemap_urls = ["https://locations.whataburger.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+\.html$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]
    search_for_facebook = False
    search_for_twitter = False

    def parse_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for day_div in response.xpath('//div[@class="Core-hoursThisWeek"]/div[@class="StoreHours"]'):
            day = day_div.xpath('./div[@class="StoreHours-day"]/span[@class="StoreHours-dayText"]/text()').get()
            for theme in day_div.xpath('./div[@class="StoreHours-container"]'):
                if theme.xpath('.//span[@class="StoreHours-nameText"]/text()').get() != "Dine In":
                    continue
                if theme.xpath('.//span[@class="StoreHours-closedText"]/text()').get() == "Closed":
                    oh.set_closed(day)
                else:
                    for times in theme.xpath('.//span[@class="StoreHours-intervals-instance"]'):
                        if times.xpath('./text()').get() == "24 hr":
                            oh.add_range(day, "00:00","23:59")
                        else:
                            oh.add_range(
                            day,
                            times.xpath('.//span[@class="StoreHours-intervals-instance-open"]/text()').get(),
                            times.xpath('.//span[@class="StoreHours-intervals-instance-close"]/text()').get(),
                            "%I:%M%p",
                        )
        return oh

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if "#" in item["name"]:
            item["ref"] = item.pop("name").split("#", 1)[1].strip()
        item["image"] = item["name"] = None
        name = response.xpath('//span[@class="Banner-titleGeo"]/text()').extract_first()
        if name == "NA":
            name = None
        item["branch"] = name

        item["opening_hours"] = self.parse_hours(response)
        apply_category(Categories.FAST_FOOD, item)

        yield item
