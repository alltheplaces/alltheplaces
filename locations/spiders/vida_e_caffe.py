import chompjs

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import OpeningHours, sanitise_day
from locations.json_blob_spider import JSONBlobSpider


class VidaECaffeSpider(JSONBlobSpider):
    name = "vida_e_caffe"
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

        if location["store_type"] == ["vending"]:
            # Beverage only? Vending machine only? Unclear
            return

        item["branch"] = item.pop("name")

        if isinstance(location["location"], dict):
            item["housenumber"] = location["location"].get("street_number")
            item["street"] = location["location"].get("street_name")
            item["city"] = location["location"].get("city")
            item["postcode"] = location["location"].get("post_code")
            item["state"] = location["location"].get("state")
            item["country"] = location["location"].get("country_short")
            item["addr_full"] = location["location"].get("address")
        if item["housenumber"] is None:
            item["housenumber"] = location["shop_number"]

        if "times" in location and location["times"]:
            item["opening_hours"] = OpeningHours()
            for time in location["times"]:
                if time["times"] == "Open 24 hours":
                    item["opening_hours"].add_ranges_from_string(time["label"] + " 00:00-23:59")
                elif "closed" in time["times"].lower():
                    day = sanitise_day(time["label"])
                    if day:
                        item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_ranges_from_string(time["label"] + " " + time["times"])

        # Features
        # 'store_features': ['free-wifi', 'halaal', 'mobile-payment', 'redeem-vitality-rewards'
        apply_yes_no(Extras.WIFI, item, "free-wifi" in location["store_features"])
        apply_yes_no(Extras.HALAL, item, "halaal" in location["store_features"])

        # Mobile payment?
        apply_yes_no(PaymentMethods.APP, item, "mobile-payment" in location["store_features"])

        yield item
