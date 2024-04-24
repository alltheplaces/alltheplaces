from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, day_range
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import FIREFOX_LATEST


class ReiUSSpider(SitemapSpider, StructuredDataSpider):
    name = "rei_us"
    item_attributes = {"brand": "REI", "brand_wikidata": "Q3414933", "country": "US"}
    allowed_domains = ["www.rei.com"]
    sitemap_urls = ["https://www.rei.com/sitemap-stores.xml"]
    sitemap_rules = [(r"^https://www.rei.com/stores/([^/]+)$", "parse_sd")]
    user_agent = FIREFOX_LATEST
    download_delay = 2.5
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["branch"] = item.pop("name")

        item["opening_hours"] = OpeningHours()
        for rule in ld_data.get("openingHours", []):
            days, times = rule.rsplit(" ", 1)
            if "-" in days:
                start_day, end_day = days.split(" - ")
            else:
                start_day = end_day = days
            item["opening_hours"].add_days_range(day_range(start_day, end_day), *times.split("-"))
        yield item
