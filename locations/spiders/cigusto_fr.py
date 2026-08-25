from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CigustoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "cigusto_fr"
    item_attributes = {"brand": "Cigusto", "brand_wikidata": "Q120785690"}
    sitemap_urls = ["https://www.cigusto.com/sitemap.xml"]
    sitemap_rules = [("/magasins/magasin-", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # NSI has exactly one Cigusto entry (only covering "fx", the legacy
        # code for Metropolitan France that the location matcher does not
        # alias to "fr"), so apply the category directly rather than relying
        # on NSI location matching.
        apply_category(Categories.SHOP_E_CIGARETTE, item)
        yield item
