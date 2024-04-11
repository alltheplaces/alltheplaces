from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class HaggenSpider(SitemapSpider, StructuredDataSpider):
    name = "haggen"
    item_attributes = {
        "brand": "Haggen",
        "brand_wikidata": "Q5638683",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["haggen.com"]
    sitemap_urls = ["https://local.haggen.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["GroceryStore"]
