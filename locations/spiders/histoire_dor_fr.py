from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HistoireDorFRSpider(SitemapSpider, StructuredDataSpider):
    name = "histoire_dor_fr"
    item_attributes = {"brand": "Histoire d'Or", "brand_wikidata": "Q62529245"}
    sitemap_urls = ["https://www.histoiredor.com/sitemap_index.xml"]
    sitemap_rules = [(r"/details/magasin/", "parse_sd")]
    wanted_types = ["JewelryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Histoire dʼOr - ", "")
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
