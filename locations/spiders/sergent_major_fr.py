from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SergentMajorFRSpider(CrawlSpider, StructuredDataSpider):
    name = "sergent_major_fr"
    item_attributes = {"brand": "Sergent Major", "brand_wikidata": "Q62521738"}
    start_urls = ["https://boutiques.sergent-major.com/fr/france-FR/all"]
    rules = [Rule(LinkExtractor(allow=r"/details$"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Sergent Major ")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
