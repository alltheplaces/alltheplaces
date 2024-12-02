import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.great_wall_motor_au_nz import GREAT_WALL_MOTOR_SHARED_ATTRIBBUTES

GWM_BRANDS = {
    "NEWGWM": GREAT_WALL_MOTOR_SHARED_ATTRIBBUTES,
    "NEWGWMHAVAL": {
        "brand": "GWM;Haval",
        "brand_wikidata": "Q1117001;Q28223947",
    },
    "NEWHAVAL": {
        "brand": "Haval",
        "brand_wikidata": "Q28223947",
    },
}


class GreatWallMotorBWNAZASpider(JSONBlobSpider):
    name = "great_wall_motor_bw_na_za"
    item_attributes = {
        "brand": "GWM",
        "brand_wikidata": "Q1117001",
    }
    start_urls = [
        "https://www.gwm.co.za/_next/static/chunks/6008-111c581cb1050b46.js",
    ]
    no_refs = True

    def extract_json(self, response):
        return chompjs.parse_js_object(response.text.split("let p=")[1])

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["addr_full"] = location["location"]
        item["website"] = "https://www.gwm.co.za"
        try:
            int(item["addr_full"].split(",")[-1])
            item["postcode"] = item["addr_full"].split(",")[-1]
            item["city"] = item["addr_full"].split(",")[-2]
        except:
            pass
        if item["state"] in ["Namibia", "Botswana"]:
            item.pop("state")
        if location["category"] == "Dealership":
            apply_category(Categories.SHOP_CAR, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_category/{location['category']}")
        if brand := GWM_BRANDS.get(location["floorcode"]):
            item.update(brand)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{location['floorcode']}")
        yield item
