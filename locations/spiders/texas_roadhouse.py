from locations.storefinders.nomnom import NomNomSpider


class TexasRoadhouseSpider(NomNomSpider):
    name = "texas_roadhouse"
    item_attributes = {
        "brand": "Texas Roadhouse",
        "brand_wikidata": "Q7707945",
    }
    start_urls = ["https://www.texasroadhouse.com/api/stores"]
