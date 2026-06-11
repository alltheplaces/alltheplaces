from locations.storefinders.yext_answers import YextAnswersSpider


class LacosteSpider(YextAnswersSpider):
    name = "lacoste"
    item_attributes = {"brand": "Lacoste", "brand_wikidata": "Q309031"}
    api_key = "838385fd3ca042db80e71cce34e3d417"
    api_version = "20220511"
    environment = "PRODUCTION"
    experience_key = "locator-search-eu"
    locale = "en-US"
