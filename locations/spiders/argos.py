from locations.storefinders.yext_answers import YextAnswersSpider


class ArgosSpider(YextAnswersSpider):
    name = "argos"
    item_attributes = {"brand": "Argos", "brand_wikidata": "Q4789707"}
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    experience_key = "argos-locator"
    api_key = "5295de161feec2b9e1ca6f483e9f77dd"
    locale = "en-GB"
