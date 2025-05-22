from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class BleuLibelluleFRSpider(SitemapSpider, StructuredDataSpider):
    name = "bleu_libellule_fr"
    item_attributes = {"brand": "Bleu Libellule", "brand_wikidata": "Q101830610"}
    sitemap_urls = ["https://magasins.bleulibellule.com/sitemap.xml"]
    sitemap_rules = [(r"magasins\.bleulibellule\.com/[-\w]+/[-\w]+/[-\w]+/[-\w]+", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Bleu Libellule ")
        yield item
