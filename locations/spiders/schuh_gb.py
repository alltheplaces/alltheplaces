from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SchuhGBSpider(SitemapSpider, StructuredDataSpider):
    name = "schuh_gb"
    item_attributes = {"brand": "Schuh", "brand_wikidata": "Q7432952"}
    sitemap_urls = ["https://www.schuh.co.uk/googleSitemap.aspx"]
    sitemap_rules = [(r"/stores/[^/]+/$", "parse")]
    wanted_types = ["ShoeStore"]
    requires_proxy = True
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def _get_sitemap_body(self, response):
        if response.url.split("?")[0].endswith(".aspx"):
            return response.body
        return super()._get_sitemap_body(response)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["facebook"] = None
        item["twitter"] = None
        item["branch"] = item.pop("name")
        item["ref"] = item["branch"]
        yield item
