from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CreditCooperatifSpider(CrawlSpider, StructuredDataSpider):
    name = "credit_cooperatif"
    item_attributes = {
        "brand": "Crédit Coopératif",
        "brand_wikidata": "Q3006190",
    }
    allowed_domains = ["agences.credit-cooperatif.coop"]
    start_urls = [
        "https://agences.credit-cooperatif.coop/banque/agences/toutes-nos-agences",
    ]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://agences.credit-cooperatif.coop/banque/agences/agences-.*-[0-9]{2}"),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r"https://agences.credit-cooperatif.coop/banque/agences/agence-.*-id[0-9]+"),
            callback="parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        apply_category(Categories.BANK, item)
        # Fix an issue in the structured data website
        item["website"] = response.url
        yield item
