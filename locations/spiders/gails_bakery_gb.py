from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories
from locations.items import Feature


class GailsBakeryGBSpider(Spider):
    name = "gails_bakery_gb"
    item_attributes = {"brand": "GAIL's Bakery", "brand_wikidata": "Q110662562", "extras": Categories.SHOP_BAKERY.value}
    start_urls = ["https://gails.com/pages/find-us"]

    def parse(self, response):
        scripts = response.xpath("//script").getall()
        for script in scripts:
            if "window.Shopify.stores" in script:
                data = parse_js_object(script)
                break
        for store in data.get("features", []):
            item = Feature()
            item["geometry"] = store["geometry"]
            props = store.get("properties", {})
            item["ref"] = props["storeid"]
            item["street_address"] = props["address1"] + props["address2"]
            item["city"] = props["city"]
            item["image"] = props["image"]
            item["name"] = props["name"]
            item["postcode"] = props["zip"]

            yield item
