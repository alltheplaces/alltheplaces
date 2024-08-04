from locations.storefinders.momentfeed import MomentFeedSpider


class VisionworksSpider(MomentFeedSpider):
    name = "visionworks"
    allowed_domains = ["visionworks.com", "api.momentfeed.com"]
    item_attributes = {"brand": "Visionworks", "brand_wikidata": "Q5422607"}
    id = "URTGGJIFYMDMAMXQ"
