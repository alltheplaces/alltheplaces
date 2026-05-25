from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class KateSpadeSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "kate_spade"
    item_attributes = {"brand": "Kate Spade New York", "brand_wikidata": "Q6375797"}
    sitemap_urls = [
        "https://www.katespade.com/stores/sitemap.xml",
        "https://www.katespade.de/stores/sitemap.xml",
        "https://www.katespade.co.uk/stores/sitemap.xml",
        "https://www.katespade.eu/be/stores/sitemap.xml",
        "https://www.katespade.eu/ie/stores/sitemap.xml",
        "https://www.katespade.eu/nl/stores/sitemap.xml",
        "https://www.katespade.eu/at/stores/sitemap.xml",
    ]
    sitemap_rules = [(r"/stores/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS
    drop_attributes = {"facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("About ")
        yield item
