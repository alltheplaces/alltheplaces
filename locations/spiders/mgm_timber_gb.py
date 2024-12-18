from locations.categories import Categories, apply_category
from locations.storefinders.yext_answers import YextAnswersSpider
from locations.pipelines.address_clean_up import merge_address_lines


class MgmTimberGBSpider(YextAnswersSpider):
    name = "mgm_timber_gb"
    item_attributes = {"brand": "MGM Timber", "brand_wikidata": ""}
    api_key = "db9fb251f6697c5529b02e93d68f6e33"
    experience_key = "donaldson-locator"
    locale = "en_GB"

    def parse_item(self, location, item):
        apply_category(Categories.TRADE_BUILDING_SUPPLIES, item)
        slug = location["slug"]
        item["website"] = f"https://www.mgmtimber.co.uk/branch-locator/{slug}"
        item["street_address"] = merge_address_lines([location["address"]["line1"], location["address"].get("line2")])
        yield item
