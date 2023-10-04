import html
import re

from chompjs import chompjs
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class JustGroupSpider(Spider):
    name = "just_group"
    allowed_domains = ["justjeans.jgl.com.au"]
    start_urls = ["https://justjeans.jgl.com.au/shop/stores"]
    brands = {
        "Dotti": "Q5299495",
        "Jacqui E": "Q118383260",
        "Jay Jays": "Q6166759",
        "Just Jeans": "Q6316068",
        "Peter Alexander": "Q118383240",
        "Portmans": "Q118383252",
        "Smiggle": "Q7544536",
    }

    def parse(self, response):
        store_data = response.xpath('//title[text()="Just Jeans Store Locations"]/following::script/text()').get()
        locations = chompjs.parse_js_object(store_data)
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["locId"]
            for brand_name, brand_wikidata in self.brands.items():
                if brand_name in item["name"]:
                    item["brand"] = brand_name
                    item["brand_wikidata"] = brand_wikidata
            item["street_address"] = html.unescape(
                ", ".join(filter(None, [location["shopAddress"], location["streetAddress"]]))
            ).replace(",,", "")
            if item["country"] == "SG":
                if m := re.search(r"\s+(\d{6})", location["city"]):
                    item["postcode"] = m.group(1)
                item.pop("city")
            item["postcode"] = item.pop("postcode").strip()
            if item["postcode"] == ".":
                item.pop("postcode")
            if item["state"] in ["NA", "N/A"]:
                item.pop("state")
            if location["suburb"].strip() == item.get("city"):
                location["suburb"] = None
            item["addr_full"] = ", ".join(
                filter(
                    None,
                    [
                        item.get("street_address"),
                        location["suburb"],
                        item.get("city"),
                        item.get("state"),
                        item.get("postcode"),
                        location["countryName"],
                    ],
                )
            ).replace(",,", "")
            item["phone"] = item.pop("phone").strip()
            item["website"] = location["storeURL"]
            hours_html = Selector(text=html.unescape(location["storehours"]))
            hours_string = " ".join(
                hours_html.xpath('//div[contains(@class, "stores__schedule")]/div/text()').getall()
            ).strip()
            if hours_string:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours_string)

            if item["brand"] == "Smiggle":
                apply_category(Categories.SHOP_STATIONERY, item)
            else:
                apply_category(Categories.SHOP_CLOTHES, item)

            yield item
