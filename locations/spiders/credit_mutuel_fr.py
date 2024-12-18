from scrapy import Request

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class CreditMutuelFRSpider(StructuredDataSpider):
    name = "credit_mutuel_fr"
    item_attributes = {"brand": "Crédit Mutuel", "brand_wikidata": "Q642627", "extras": Categories.BANK.value}
    allowed_domains = ["www.creditmutuel.fr"]
    start_urls = ["https://www.creditmutuel.fr/fr/sitemap-cm-caisses.txt"]
    custom_settings = {"REDIRECT_ENABLED": False}

    def parse(self, response):
        for url in response.text.splitlines():
            yield Request(url=url, callback=self.parse_sd)
