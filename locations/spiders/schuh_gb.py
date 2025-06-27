from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class SchuhGBSpider(SitemapSpider, StructuredDataSpider):
    name = "schuh_gb"
    item_attributes = {"brand": "Schuh", "brand_wikidata": "Q7432952"}
    sitemap_urls = ["https://www.schuh.co.uk/googleSitemap.aspx"]
    sitemap_rules = [(r"/stores/[^/]+/$", "parse")]
    wanted_types = ["ShoeStore"]
    requires_proxy = True
    user_agent = BROWSER_DEFAULT
    custom_settings = {
        # somehow this actually seems to work
        "RETRY_HTTP_CODES": [403],
    }

    def _get_sitemap_body(self, response):
        if response.url.split("?")[0].endswith(".aspx"):
            return response.body
        return super()._get_sitemap_body(response)
