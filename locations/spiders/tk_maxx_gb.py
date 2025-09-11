from locations.storefinders.yext_answers import YextAnswersSpider


class TkMaxxGBSpider(YextAnswersSpider):
    name = "tk_maxx_gb"
    item_attributes = {"brand": "TK Maxx", "brand_wikidata": "Q23823668"}
    api_key = "ce8e33e14f7f6706a1a86e05e440d1a0"
    experience_key = "tk-maxx-search-experience"
    feature_type = "locations"
