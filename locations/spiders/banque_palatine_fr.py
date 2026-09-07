from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category


class BanquePalatineFRSpider(CrawlSpider, StructuredDataSpider):
    name = "banque_palatine_fr"
    item_attributes = {
        "brand": "Q2883429",
        "brand_wikidata": "Q2883429",
    }
    allowed_domains = ["agences.palatine.fr"]
    start_urls = ["https://agences.palatine.fr/toutes-nos-agences"]
    rules = [
        Rule(
            LinkExtractor(allow=r"-id[0-9]+$"),
            callback="parse_sd",
            follow=False,
        ),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    drop_attributes = ["image"]


    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.BANK, item)
        if item.get("email","") == "contact@palatine.fr":
            item.pop("email")

        item["branch"] = item.pop("name", "")
        
        yield item
