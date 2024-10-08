from locations.storefinders.yext_answers import YextAnswersSpider


class WarbyParkerSpider(YextAnswersSpider):
    name = "warby_parker"
    experience_key = "warby-parker-search"
    api_key = "5547ae84dd10f10663a8a5d13f71fd9a"
    item_attributes = {"brand": "Warby Parker", "brand_wikidata": "Q7968882"}
