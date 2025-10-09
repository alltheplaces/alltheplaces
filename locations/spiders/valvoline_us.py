from locations.storefinders.yext_answers import YextAnswersSpider


class ValvolineUSSpider(YextAnswersSpider):
    name = "valvoline_us"
    item_attributes = {"brand": "Valvoline", "brand_wikidata": "Q7912852"}
    drop_attributes = {"name"}
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    api_key = "6be872666a9f219fe05526bbd5ece9c5"
    experience_key = "main-site-locator"
    locale = "en"
