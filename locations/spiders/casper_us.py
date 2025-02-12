from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class CasperUSSpider(SitemapSpider, StructuredDataSpider):
    name = "casper_us"
    item_attributes = {"brand": "Casper", "brand_wikidata": "Q20539294", "extras": Categories.SHOP_BED.value}
    sitemap_urls = ["https://stores.casper.com/sitemap.xml"]
    sitemap_rules = [(r"stores\.casper\.com\/casper\-.*$", "parse_sd")]
    wanted_types = ["HomeGoodsStore"]
    drop_attributes = {"image"}
