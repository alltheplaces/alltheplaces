import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HannafordSpider(SitemapSpider, StructuredDataSpider):
    name = "hannaford"
    item_attributes = {"brand": "Hannaford"}
    allowed_domains = ["hannaford.com"]
    sitemap_urls = ["https://stores.hannaford.com/sitemap.xml"]
    sitemap_rules = [(r"[0-9]+$", "parse_sd")]
    wanted_types = ["GroceryStore"]

    def inspect_item(self, item, response):
        days = json.loads(response.xpath('//h4[text()="Store Hours"]/following::div[1]/@data-days').get())
        oh = OpeningHours()
        for day in days:
            opentime = str(day.get("intervals")[0].get("start")).zfill(4)
            closetime = str(day.get("intervals")[0].get("end")).zfill(4)
            oh.add_range(
                day=day.get("day"),
                open_time=f"{opentime[:2]}:{opentime[2:]}",
                close_time=f"{closetime[:2]}:{closetime[2:]}",
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
