import chompjs

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class VidaCaffeSpider(JSONBlobSpider):
    name = "vida_caffe"
    item_attributes = {
        "brand": "Vida e Caffè",
        "brand_wikidata": "Q7927650",
    }
    start_urls = ["https://vidaecaffe.com/contact/stores/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[@type="rocketlazyloadscript" and contains(text(), "var stores = ")]/text()').get()
        )

    def post_process_item(self, item, response, location):
        # {'id': 353, 'title': '@Home Sandton City', 'location': {'address': 'Sandton City, 163 5th St, Sandhurst, Sandton, GP, South Africa', 'lat': '-26.1082596', 'lng': '28.0531383'}, 'images': False, 'email': 'athomesandton@Caffe.co.za', 'facebook': None, 'times': False, 'shop_number': 'Shop U307', 'contact_number': '', 'store_type': ['corporate'], 'store_features': []}

        if location["store_type"] == "vending":
            # Beverage only? Vending machine only? Unclear
            return

        item["housenumber"] = location["shop_number"]
        if "Times" in location and location["Times"]:
            item["opening_hours"] = OpeningHours()
            for time in location["Times"]:
                item["opening_hours"].add_ranges_from_string(time["label"] + " " + time["times"])

        # Features
        # 'store_features': ['free-wifi', 'halaal', 'mobile-payment', 'redeem-vitality-rewards'
        apply_yes_no(Extras.WIFI, item, "free-wifi" in location["store_features"])
        apply_yes_no(Extras.HALAL, item, "halaal" in location["store_features"])

        # Mobile payment?
        apply_yes_no(PaymentMethods.APP, item, "mobile-payment" in location["store_features"])

        yield item
