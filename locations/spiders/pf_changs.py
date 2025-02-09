from locations.storefinders.yext_answers import YextAnswersSpider


class PfChangsSpider(YextAnswersSpider):
    name = "pf_changs"
    item_attributes = {"brand": "P.F. Chang's", "brand_wikidata": "Q5360181"}
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    api_key = "74fc62da2a16bf5d87424b94f3bfddcc"
    experience_key = "locator"
    feature_type = "restaurants"
    drop_attributes = {"contact:instagram", "twitter"}
