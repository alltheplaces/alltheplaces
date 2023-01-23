from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class BanquePopulaireSpider(CrawlSpider, StructuredDataSpider):
    name = "banquepopulaire"
    item_attributes = {"brand": "banquepopulaire", "brand_wikidata": "Q846647"}
    start_urls = ["https://agences.banquepopulaire.fr/banque-assurance/toutes-nos-agences"]
    allowed_domains = ["agences.banquepopulaire.fr"]
    rules = [
        Rule(LinkExtractor(allow=r"C[0-9]+$"), follow=True),
        Rule(LinkExtractor(allow=r"id[0-9]+$"), callback="parse_sd", follow=True),
    ]
