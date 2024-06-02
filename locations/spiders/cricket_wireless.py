from locations.storefinders.momentfeed import MomentFeedSpider


class CricketWirelessSpider(MomentFeedSpider):
    name = "cricket_wireless"
    item_attributes = {"brand": "Cricket Wireless", "brand_wikidata": "Q5184987"}
    api_key = "IVNLPNUOBXFPALWE"
