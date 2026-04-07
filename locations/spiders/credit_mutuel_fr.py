from copy import deepcopy

from scrapy import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class CreditMutuelFRSpider(StructuredDataSpider):
    name = "credit_mutuel_fr"
    item_attributes = {"brand": "Crédit Mutuel", "brand_wikidata": "Q642627"}
    allowed_domains = ["www.creditmutuel.fr"]
    start_urls = ["https://www.creditmutuel.fr/fr/sitemap-cm-caisses.txt"]
    custom_settings = {"REDIRECT_ENABLED": True}

    def parse(self, response):
        for url in response.text.splitlines():
            yield Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        has_atm = bool(response.css(".ei_rogi_picto_withdrawal_bills_eur").get())

        if has_atm:
            atm_item = deepcopy(item)
            atm_item["ref"] += "-ATM"
            apply_category(Categories.ATM, atm_item)
            yield atm_item

        apply_category(Categories.BANK, item)
        apply_yes_no(Extras.ATM, item, has_atm)
        yield item
