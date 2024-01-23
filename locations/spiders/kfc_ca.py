from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.spiders.kfc import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class KFCCASpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_ca"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["kfc.ca"]
    sitemap_urls = ["https://www.kfc.ca/sitemap.xml"]
    sitemap_rules = [("/store/", "parse_sd")]
    user_agent = BROWSER_DEFAULT
    requires_proxy = "CA"

    def pre_process_data(self, ld_data, **kwargs):
        oh = OpeningHours()

        for rule in ld_data.get("openingHours", []):
            day, times = rule.split(" ", maxsplit=1)
            if "n/a" in times.lower():
                continue
            start_time, end_time = times.split("-")
            try:
                oh.add_range(day, start_time, end_time, time_format="%I:%M %p")
            except:
                continue

        ld_data["openingHours"] = oh.as_opening_hours()

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = item["addr_full"]
        item["addr_full"] += ", " + response.xpath('//span[@class="postal-code"]/text()').get()

        yield item
