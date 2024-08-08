from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class VanharenBENLSpider(SitemapSpider, StructuredDataSpider):
    name = "vanharen_be_nl"
    item_attributes = {"brand_wikidata": "Q62390668", "brand": "vanHaren", "extras": Categories.SHOP_SHOES.value}
    sitemap_urls = ["https://stores.vanharen.nl/sitemap.xml"]
    sitemap_rules = [
        (r"-\d+$", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
