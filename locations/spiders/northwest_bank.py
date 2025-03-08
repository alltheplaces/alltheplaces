from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.yext_answers import YextAnswersSpider


class NorthwestBankSpider(YextAnswersSpider):
    name = "northwest_bank"
    item_attributes = {"brand": "Northwest Bank", "brand_wikidata": "Q7060191"}
    api_key = "3f2b988212750727a2baf6570b5e4579"
    experience_key = "northwest-bank-answers"
    facet_filters = {"c_locationType": [{"c_locationType": {"$eq": "Northwest Bank Branch & ATM"}}]}

    def parse_item(self, location, item):
        if item["name"].endswith(" ATM"):
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)

        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in location.get("c_availableServices", []))
        item["image"] = location.get("c_locationImage", {}).get("url")
        item["facebook"] = location.get("facebookPageUrl")

        yield item
