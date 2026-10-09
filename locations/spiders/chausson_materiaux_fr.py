from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ChaussonMateriauxFRSpider(SitemapSpider, StructuredDataSpider):
    name = "chausson_materiaux_fr"
    item_attributes = {"brand": "Chausson Matériaux", "brand_wikidata": "Q100701530"}
    sitemap_urls = ["https://www.chausson.fr/sitemap-agencies.xml"]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "")

        apply_category(Categories.SHOP_TRADE, item)

        yield item
