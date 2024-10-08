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
        "https://www.gwm.co.za/_next/static/chunks/132-327146a73ab927d0.js",
        "https://www.haval.co.za/_next/static/chunks/7645-1ac3fce7750412a0.js",
    ]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.text.split("let a=")[1])

    def post_process_item(self, item, response, location):
        item["ref"] = location["cmscode"]
        item["branch"] = item.pop("name")
        item["addr_full"] = location["location"]
        try:
            int(item["addr_full"].split(",")[-1])
            item["postcode"] = item["addr_full"].split(",")[-1]
            item["city"] = item["addr_full"].split(",")[-2]
        except:
            pass
        if location["category"] == "Dealership":
            apply_category(Categories.SHOP_CAR, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_category/{location['category']}")
        if brand := GWM_BRANDS.get(location["floorcode"]):
            item.update(brand)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{location['floorcode']}")
        yield item
