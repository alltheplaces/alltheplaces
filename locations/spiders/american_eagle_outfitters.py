from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AmericanEagleOutfittersSpider(SitemapSpider, StructuredDataSpider):
    name = "american_eagle_outfitters"
    item_attributes = {"brand": "American Eagle Outfitters", "brand_wikidata": "Q2842931"}
    AERIE = {"brand": "Aerie", "brand_wikidata": "Q25351619"}
    OFFLINE = {"brand": "OFFLINE By Aerie", "brand_wikidata": ""}
    sitemap_urls = ["https://stores.aeostores.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        brand = ld_data.get("brand", "").title()
        if brand.startswith("Aerie"):
            item.update(self.AERIE)
        elif brand.startswith("Offline"):
            item.update(self.OFFLINE)
            apply_category(Categories.SHOP_CLOTHES, item)
        yield item
