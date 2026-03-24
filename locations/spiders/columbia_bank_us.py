from locations.categories import Categories, apply_category
from locations.storefinders.yext_answers import YextAnswersSpider


class ColumbiaBankUSSpider(YextAnswersSpider):
    name = "columbia_bank_us"
    item_attributes = {
        "brand": "Columbia Bank",
        "brand_wikidata": "Q7881772",
    }
    api_key = "c13432212bdffaaf25baa76819280ae4"
    experience_key = "umpqua-bank-locator"
    drop_attributes = {"facebook", "branch", "contact:instagram"}

    def parse_item(self, location, item):
        if item["name"] == "ATM - Columbia Bank":
            del item["name"]
            item.pop("website", None)  # ATM website is always the homepage
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        yield item
