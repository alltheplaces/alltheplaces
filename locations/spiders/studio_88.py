from locations.spiders.ok_furniture import OkFurnitureSpider


class Studio88Spider(OkFurnitureSpider):
    name = "studio_88"
    item_attributes = {"brand": "Studio 88", "brand_wikidata": "Q116498145"}
    allowed_domains = ["studio-88.co.za"]
    start_urls = ["https://www.studio-88.co.za/store-locator/"]
    requires_proxy = "ZA"
