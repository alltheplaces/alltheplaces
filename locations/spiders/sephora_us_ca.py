from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SephoraUSCASpider(SitemapSpider, StructuredDataSpider):
    name = "sephora_us_ca"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    allowed_domains = ["www.sephora.com"]
    sitemap_urls = ["https://www.sephora.com/sephora-store-sitemap.xml"]
    sitemap_rules = [(r"\/happening\/stores\/(?!kohls).+", "parse_sd")]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data):
        item.pop("image")
        hours_string = " ".join(ld_data["openingHours"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
