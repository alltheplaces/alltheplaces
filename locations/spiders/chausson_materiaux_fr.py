from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class ChaussonMateriauxFrSpider(SitemapSpider, StructuredDataSpider):
    name = "chausson_materiaux_fr"
    item_attributes = {"brand": "Chausson Matériaux", "brand_wikidata": "Q100701530"}
    sitemap_urls = ["https://www.chausson.fr/sitemap-agencies.xml"]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_TRADE, item)
        apply_category(Categories.TRADE_BUILDING_SUPPLIES, item)
        item["branch"] = item.pop("name","")

        yield item
