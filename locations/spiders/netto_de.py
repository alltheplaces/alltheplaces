from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import FIREFOX_LATEST


class NettoDESpider(SitemapSpider, StructuredDataSpider):
    name = "netto_de"
    allowed_domains = ["netto-online.de"]
    sitemap_urls = ["https://www.netto-online.de/ueber-netto/sitemap/index"]
    sitemap_rules = [(r"/filialen/[^/]+/[^/]+/(\d+)/$", "parse")]
    wanted_types = ["GroceryStore"]
    user_agent = FIREFOX_LATEST
    custom_settings = {"DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"}}

    categories = {
        "Netto City": Categories.SHOP_SUPERMARKET,
        "Netto Getränke-Discount": Categories.SHOP_BEVERAGES,
        "Netto Marken-Discount": Categories.SHOP_SUPERMARKET,
    }

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["brand"] = item["name"] = ld_data["name"].split(" - ", 1)[0]
        if cat := self.categories.get(item["brand"]):
            apply_category(cat, item)
        else:
            self.crawler.stats.inc_value("{}/unknown_type/{}".format(self.name, item["brand"]))
            self.logger.error("Unknown type: {}".format(ld_data["name"]))

        yield item
