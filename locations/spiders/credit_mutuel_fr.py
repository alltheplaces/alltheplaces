from scrapy import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class CreditMutuelFRSpider(StructuredDataSpider):
    name = "credit_mutuel_fr"
    item_attributes = {"brand": "Crédit Mutuel", "brand_wikidata": "Q642627"}
    allowed_domains = ["www.creditmutuel.fr"]
    start_urls = ["https://www.creditmutuel.fr/fr/sitemap-cm-caisses.txt"]

    def parse(self, response):
        for url in response.text.splitlines():
            yield Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.BANK, item)
        apply_yes_no(Extras.ATM, item, bool(response.css(".ei_rogi_picto_withdrawal_bills_eur").get()))
        yield item
