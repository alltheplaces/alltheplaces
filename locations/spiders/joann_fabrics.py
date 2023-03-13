from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JoAnnFabricsSpider(SitemapSpider, StructuredDataSpider):
    name = "joann_fabrics"
    item_attributes = {"brand": "Jo-Ann Fabrics", "brand_wikidata": "Q6203968"}
    sitemap_urls = ["https://stores.joann.com/robots.txt"]
    sitemap_rules = [(r"/\d+/", "parse_sd")]
    wanted_types = ["HobbyShop"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["image"] = None
