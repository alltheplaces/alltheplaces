from locations.storefinders.yext_answers import YextAnswersSpider


class ShepherdNeameSpider(YextAnswersSpider):
    name = "shepherd_neame"
    item_attributes = {"brand": "Shepherd Neame", "brand_wikidata": "Q12002324"}
    endpoint = "https://prod-cdn.eu.yextapis.com/v2/accounts/me/search/vertical/query"
    experience_key = "search-copy"
    api_key = "b81096dc4941844b0b98616f9a715358"
    locale = "en-GB"
    v = "20220511"
    feature_type = "restaurants"
