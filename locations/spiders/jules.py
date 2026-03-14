from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Clothes, apply_clothes
from locations.structured_data_spider import StructuredDataSpider


class JulesSpider(CrawlSpider, StructuredDataSpider):
    name = "jules"
    item_attributes = {"brand": "Jules", "brand_wikidata": "Q3188386"}
    start_urls = [
        "https://www.jules.com/fr-be/recherche-magasins/",
        "https://www.jules.com/fr-fr/recherche-magasins/",
    ]
    rules = [Rule(LinkExtractor(allow="/magasins/"), callback="parse", follow=True)]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        item["branch"] = item.pop("name").replace("BRICE - ", "").replace("JULES - ", "")
        apply_clothes([Clothes.MEN], item)
        yield item
