from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SixtSpider(SitemapSpider, StructuredDataSpider):
    name = "sixt"
    item_attributes = {"brand": "Sixt", "brand_wikidata": "Q705664"}
    sitemap_urls = ["https://www.sixt.co.uk/sitemap_index.xml"]
    sitemap_rules = [(r"\/car-hire\/[-\w]+\/[-\w]+\/[-\w]+\/$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    sitemap_follow = ["/car-hire/"]
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["country"] = item.pop("state")

        yield item
