from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class ChausseaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "chaussea_fr"
    item_attributes = {"brand": "Chaussea", "brand_wikidata": "Q62082044"}
    sitemap_urls = ["https://www.chaussea.com/modules/chssitemap/sitemaps/fr-fr-magasins.xml"]
    sitemap_rules = [(r"/fr/magasin/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_SHOES, item)

        yield item
