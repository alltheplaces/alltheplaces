from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SixtSpider(SitemapSpider, StructuredDataSpider):
    name = "sixt"
    item_attributes = {"brand": "SIXT", "brand_wikidata": "Q705664"}
    sitemap_urls = ["https://www.sixt.co.uk/sitemap_index.xml"]
    sitemap_rules = [(r"\/car-hire\/[-\w]+\/[-\w]+\/[-\w]+\/$", "parse_sd")]
    user_agent = BROWSER_DEFAULT
    sitemap_follow = ["/car-hire/"]
    skip_auto_cc_domain = True

    def post_process_item(self, item, response, location):
        item["country"] = item.pop("state")

        yield item
