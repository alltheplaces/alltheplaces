import json
import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StorageRentalsOfAmericaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "storage_rentals_of_america_us"
    item_attributes = {"brand": "Storage Rentals of America", "brand_wikidata": "Q120733770"}
    sitemap_urls = ["https://www.sroa.com/find-storage/sitemap.xml"]
    sitemap_rules = [(r"/find-storage/[^/]+/[^/]+/(?!storage-types$)[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"email", "image"}

    def post_process_item(self, item: Feature, response: Response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "").removeprefix("Storage Rentals of America - ")
        item["opening_hours"] = self.parse_hours(response)
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item

    @staticmethod
    def parse_hours(response: Response) -> OpeningHours:
        oh = OpeningHours()
        if match := re.search(r'leasingOfficeHours\\":(\[.*?\}\}\])', response.text):
            for rule in json.loads(match.group(1).replace('\\"', '"')):
                day = DAYS_EN.get(rule["days"])
                if not day:
                    continue
                hours = rule["hours"]
                if hours["closed"]:
                    oh.set_closed(day)
                else:
                    oh.add_range(day, hours["from"], hours["to"], "%H:%M:%S")
        return oh
