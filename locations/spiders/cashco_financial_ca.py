from locations.storefinders.sweetiq import SweetIQSpider


class CashcoFinancialCASpider(SweetIQSpider):
    name = "cashco_financial_ca"
    item_attributes = {"brand": "Cashco Financial", "brand_wikidata": "Q117314435"}
    start_urls = ["https://branchlocations.cashcofinancial.com/"]

    def parse_item(self, item, location):
        item.pop("website")
        if "branch_" not in item["email"]:
            item.pop("email")
        yield item
