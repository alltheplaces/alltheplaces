from locations.categories import Categories, apply_category
from locations.storefinders.yext_answers import YextAnswersSpider


class MgmTimberGBSpider(YextAnswersSpider):
    name = "mgm_timber_gb"
    item_attributes = {"brand": "MGM Timber", "brand_wikidata": ""}
    api_key = "db9fb251f6697c5529b02e93d68f6e33"
    experience_key = "donaldson-locator"
    locale = "en_GB"

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.TRADE_BUILDING_SUPPLIES, item)
        yield item
