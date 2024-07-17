from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class AnnTaylorUSSpider(SitemapSpider, StructuredDataSpider):
    name = "ann_taylor_us"
    item_attributes = {"brand": "Ann Taylor", "brand_wikidata": "Q4766699", "extras": Categories.SHOP_CLOTHES.value}
    drop_attributes = {"facebook"}
    allowed_domains = ["www.anntaylor.com"]
    sitemap_urls = ["https://www.anntaylor.com/sitemap_index.xml"]
    sitemap_rules = [(r"^https:\/\/www\.anntaylor\.com\/store(?:\/factory)?\/[a-z]{2}\/[\w\-]+\/[\w\-]+$", "parse_sd")]
