from locations.storefinders.yext_answers import YextAnswersSpider


class MgmTimberGBSpider(YextAnswersSpider):
    name = "mgm_timber_gb"
    item_attributes = {"brand": "MGM Timber", "brand_wikidata": ""}
    api_key = "db9fb251f6697c5529b02e93d68f6e33"
    experience_key = "donaldson-locator"
    locale = "en_GB"
