from locations.storefinders.yext_answers import YextAnswersSpider


class TgiFridaysUSSpider(YextAnswersSpider):
    name = "tgi_fridays_us"
    item_attributes = {"brand": "TGI Fridays", "brand_wikidata": "Q1524184"}
    api_key = "96b4f9cb0c9c2f050eeec613af5b5340"
    experience_key = "tgi-fridays-search"
