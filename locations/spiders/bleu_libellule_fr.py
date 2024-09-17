from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BleuLibelluleFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bleu_libellule_fr"
    item_attributes = {"brand": "Bleu Libellule", "brand_wikidata": "Q101830610"}
    sitemap_urls = ["https://magasins.bleulibellule.com/sitemap.xml"]
    sitemap_rules = [(r"fr/shop/(.*)$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
