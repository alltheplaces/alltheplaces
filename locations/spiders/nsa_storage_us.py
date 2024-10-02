import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range
from locations.structured_data_spider import StructuredDataSpider


class NsaStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "nsa_storage_us"
    sitemap_urls = ["https://www.nsastorage.com/robots.txt"]
    sitemap_rules = [("/storage/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["SelfStorage"]

    brands = {
        "Hide-Away Portable Storage": {"brand": "Hide-Away Storage"},
        "Hide-Away Storage": {"brand": "Hide-Away Storage"},
        "Moove In Self Storage": {"brand": "Moove In Self Storage"},
        "Move It Storage": {"brand": "Move It Storage"},
        "Northwest Self Storage": {"brand": "Northwest Self Storage", "brand_wikidata": "Q108576211"},
        "RightSpace Storage": {"brand": "RightSpace Storage", "brand_wikidata": "Q126952279"},
        "SecurCare Self Storage": {"brand": "SecurCare Self Storage", "brand_wikidata": "Q124821649"},
        "Southern Self Storage": {"brand": "Southern Self Storage", "brand_wikidata": "Q127598521"},
        "iStorage": {"brand": "iStorage", "brand_wikidata": "Q122721929"},
    }

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["openingHours"] = ld_data["openingHoursSpecification"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"], item["branch"] = item["name"].split(" | ", 1)

        if brand := self.brands.get(item["name"]):
            item.update(brand)
        else:
            self.crawler.stats.inc_value("{}/unknown_brand/{}".format(self.name, item["name"]))

        if m := re.search(r"lat\\u0022:(-?\d+\.\d+),\\u0022long\\u0022:(-?\d+\.\d+),", response.text):
            item["lat"], item["lon"] = m.groups()

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)

        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours | str:
        if response.xpath('//div[contains(h5/text(), "Access Hours")][contains(., "Always Open")]'):
            return "24/7"
        oh = OpeningHours()
        for rule in response.xpath('//div[contains(h5/text(), "Access Hours")]//div[contains(@class, "table-row")]'):
            days = rule.xpath('.//div[@class="name"]/text()').get()
            if " - " in days:
                days = day_range(*days.split(" - "))
            else:
                days = [days]
            times = rule.xpath('.//div[@class="val"]/text()').get()
            if times == "Closed":
                oh.set_closed(days)
            else:
                start_time, end_time = times.split(" - ", 1)
                if start_time and end_time:
                    oh.add_days_range(days, start_time, end_time, "%I:%M %p")
        return oh
