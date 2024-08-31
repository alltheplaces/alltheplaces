from locations.spiders.ok_furniture import OkFurnitureSpider


class HouseAndHomeSpider(OkFurnitureSpider):
    name = "house_and_home"
    item_attributes = {"brand": "House & Home", "brand_wikidata": "Q116520162"}
    allowed_domains = ["houseandhome.co.za"]
    start_urls = ["https://www.houseandhome.co.za/store-locator/"]
