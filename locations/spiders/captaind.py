from locations.storefinders.momentfeed import MomentFeedSpider


class CaptainDSpider(MomentFeedSpider):
    name = "captaind"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    id = "AJXCZOENNNXKHAKZ"
