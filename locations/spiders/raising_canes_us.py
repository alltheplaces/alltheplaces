from locations.storefinders.yext_answers import YextAnswersSpider


class RaisingCanesUSSpider(YextAnswersSpider):
    name = "raising_canes_us"
    item_attributes = {
        "brand_wikidata": "Q7285144",
        "brand": "Raising Cane's",
    }
    api_key = "6c78315e15b82a7cccbbf3fad5db0958"
    api_version = "20220511"
    environment = "PRODUCTION"
    experience_key = "locator"
    feature_type = "locations"
    locale = "en"
