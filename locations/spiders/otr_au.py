from scrapy import FormRequest, Spider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class OtrAUSpider(Spider):
    name = "otr_au"
    item_attributes = {"brand": "OTR", "brand_wikidata": "Q116394019"}

    def start_requests(self):
        yield FormRequest(url="https://www.otr.com.au/wp-admin/admin-ajax.php", formdata={"action": "LocationsSearch"})

    def parse(self, response, **kwargs):
        for location in response.json()["response"]:
            if location["site_closed"] != "0" or location["site_wpid"] == 0:
                continue

            clean_location = {}
            for key, value in location.items():
                clean_location[key.replace("site_", "")] = value
            location = clean_location

            location["url"] = (
                f'https://www.otr.com.au/locations/{location["suburb_url"]}-{location["streetaddress_url"]}/{location["name_url"]}/'
            )

            item = DictParser.parse(location)

            apply_yes_no("atm", item, "33" in location["offers"])
            apply_yes_no("drive_through", item, "35" in location["offers"])
            apply_yes_no(Fuel.DIESEL, item, "102" in location["offers"])
            apply_yes_no(Fuel.LPG, item, "104" in location["offers"])

            if "35" in location["offers"]:
                apply_category(Categories.FUEL_STATION, item)
            if "41" in location["offers"]:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
