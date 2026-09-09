from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GemoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "gemo_fr"
    item_attributes = {"brand": "Gémo", "brand_wikidata": "Q3122954"}
    allowed_domains = ["www.gemo.fr"]
    sitemap_urls = ["https://www.gemo.fr/Assets/Rbs/Seo/100199/fr_FR/Rbs_Store_Store.1.xml"]
    sitemap_rules = [(r"/magasin/", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    time_format = "%H:%M:%S"
    drop_attributes = {"facebook", "twitter"}  # brand-wide social links, not store specific

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
