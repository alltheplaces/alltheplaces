from locations.storefinders.storepoint import StorepointSpider


class JenningsBetGBSpider(StorepointSpider):
    name = "jennings_bet_gb"
    item_attributes = {"brand": "JenningsBet", "brand_wikidata": "Q112925339"}
    key = "16399b98112ff0"
