from locations.storefinders.yext_answers import YextAnswersSpider


class BookerGBSpider(YextAnswersSpider):
    name = "booker_gb"
    item_attributes = {"brand": "Booker", "brand_wikidata": "Q4943180"}
    api_key = "9ca92999bf86e368065b5018e3f82c74"
    experience_key = "yext-pages-locator-search"
