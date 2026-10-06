from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class ChausseaFRSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "chaussea_fr"
    item_attributes = {"brand": "Chaussea", "brand_wikidata": "Q62082044"}
    sitemap_urls = ["https://www.chaussea.com/modules/chssitemap/sitemaps/fr-fr-magasins.xml"]
    sitemap_rules = [(r"/fr/magasin/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_SHOES, item)

        yield item
