import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HannafordSpider(SitemapSpider, StructuredDataSpider):
    name = "hannaford"
    item_attributes = {"brand": "Hannaford", "brand_wikidata": "Q5648760"}
    allowed_domains = ["hannaford.com"]
    sitemap_urls = ["https://stores.hannaford.com/sitemap.xml"]
    sitemap_rules = [(r"[0-9]+$", "parse_sd")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        days = json.loads(response.xpath("//@data-days").get())
        oh = OpeningHours()
        for day in days:
            for halfday in day.get("intervals"):
                oh.add_range(
                    day=day.get("day"),
                    open_time=str(halfday.get("start")).zfill(4),
                    close_time=str(halfday.get("end")).zfill(4),
                    time_format="%H%M",
                )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
