from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class BureauValleeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bureau_vallee_fr"
    item_attributes = {
        "brand": "Bureau Vallée",
        "brand_wikidata": "Q18385014",
        "extras": Categories.SHOP_STATIONERY.value,
    }
    sitemap_urls = ["https://magasins.bureau-vallee.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"https://magasins\.bureau-vallee\.fr/fr/france-FR/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["LocalBusiness", "OfficeEquipmentStore"]
    drop_attributes = {"image", "twitter"}
