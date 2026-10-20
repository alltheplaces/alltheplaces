from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class RemoveryUSSpider(SitemapSpider, StructuredDataSpider):
    name = "removery_us"
    item_attributes = {"brand": "Removery", "brand_wikidata": "Q119982405"}
    sitemap_urls = ["https://removery.com/locations-sitemap.xml"]
    sitemap_follow = ["storelocator"]
    sitemap_rules = [(r"https://removery.com/tattoo-removal/locations/[\w-]+/[\w-]+/[\w-]+/$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item["image"] = None
        item["facebook"] = None
        item["twitter"] = None
        item.pop("name", None)
        item["opening_hours"] = self.parse_hours(response)
        apply_category(Categories.SHOP_BEAUTY_TATTOO_REMOVAL, item)
        yield item

    @staticmethod
    def parse_hours(response: Response) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('(//div[@class="location-detail__hours"])[1]/div[@class="location-detail__day"]'):
            day = rule.xpath("normalize-space(span)").get().rstrip(":")
            times = rule.xpath("normalize-space(text()[normalize-space()])").get()
            if times == "Closed":
                oh.set_closed(day)
            elif " - " in times:
                open_time, close_time = times.split(" - ")
                oh.add_range(day, open_time, close_time, "%I:%M %p")
        return oh
