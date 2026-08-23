from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class ConforamaFRSpider(SitemapSpider, StructuredDataSpider, CamoufoxSpider):
    name = "conforama_fr"
    item_attributes = {"brand": "Conforama", "brand_wikidata": "Q541134"}
    allowed_domains = ["www.conforama.fr"]
    sitemap_urls = ["https://www.conforama.fr/sitemap-magasins.xml"]
    sitemap_rules = [(r"/magasins-conforama/[\w-]+/[\w-]+$", "parse_sd")]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS
    # National call centre number shared by almost every store, not a per-branch line.
    generic_phone = "+33 892 010 808"

    def post_process_item(self, item, response, ld_data):
        item.pop("image", None)  # Same generic brand image on every store page.
        if ld_data.get("telephone") == self.generic_phone:
            item["phone"] = None
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
