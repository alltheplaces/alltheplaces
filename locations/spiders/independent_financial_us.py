from locations.categories import Categories, apply_category
from locations.storefinders.yext_answers import YextAnswersSpider


class IndependentFinancialUSSpider(YextAnswersSpider):
    name = "independent_financial_us"
    item_attributes = {"brand": "Independent Financial", "brand_wikidata": "Q6016398"}
    api_key = "ee4600854cf5501c53831bf944472e57"
    experience_key = "independent-financial-search"

    def parse_item(self, location, item):
        if location["data"]["type"] == "atm":
            apply_category(Categories.ATM, item)
        elif location["data"]["type"] == "location":
            apply_category(Categories.BANK, item)
        else:
            self.logger.error("Unknown location type: {}".format(location["data"]["type"]))
        yield item
