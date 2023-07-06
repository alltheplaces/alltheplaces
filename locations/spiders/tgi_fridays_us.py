from locations.storefinders.yext import YextSpider


class TGIFridaysUS(YextSpider):
    name = "tgi_fridays_us"
    item_attributes = {"brand": "TGI Fridays", "brand_wikidata": "Q1524184"}
    api_key = "96b4f9cb0c9c2f050eeec613af5b5340"

    def parse_item(self, item, location):
        item["name"] = location["geomodifier"]
        yield item
