from locations.storefinders.where2getit import Where2GetItSpider


class TacoJohnsUSSpider(Where2GetItSpider):
    name = "taco_johns_us"
    item_attributes = {"brand": "Taco John's", "brand_wikidata": "Q7673962"}
    api_key = "0B6C3264-4D73-11EE-A979-E3387089056E"
