from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class ExtendedStayAmericaSpider(SitemapSpider, StructuredDataSpider):
    name = "extended_stay_america"
    item_attributes = {
        "brand": "Extended Stay America",
        "brand_wikidata": "Q5421850",
        "country": "US",
    }
    sitemap_urls = ["https://api.prod.bws.esa.com/cms-proxy-api/sitemap/property"]
    sitemap_rules = [("/hotels/", "parse_sd")]
    custom_settings = {"AUTOTHROTTLE_ENABLED": True, "USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True
