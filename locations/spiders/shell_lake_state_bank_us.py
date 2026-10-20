import re

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class ShellLakeStateBankUSSpider(Spider):
    name = "shell_lake_state_bank_us"
    item_attributes = {"brand": "Shell Lake State Bank", "name": "Shell Lake State Bank", "country": "US"}
    start_urls = ["https://shelllakestatebank.com/hours-locations/"]

    @staticmethod
    def address_key(address: str) -> tuple:
        housenumber = re.match(r"(\d+)(?=\s)", address)
        postcode = re.search(r"\d{5}$", address)
        return (housenumber.group(1) if housenumber else None, postcode.group() if postcode else None)

    def parse(self, response: Response):
        script = response.xpath('//script[contains(text(), "var stores")]/text()').get()
        stores = parse_js_object(script[script.index("var stores") :])
        stores_by_address = {self.address_key(store["address"]): store for store in stores}

        matched_addresses = set()
        for caption in response.css("div.contentCol div.caption"):
            if not caption.css("a[href*='maps.app.goo.gl']"):
                # The "Helpful Information" caption has no store address and isn't a branch.
                continue

            texts = [t.strip() for t in caption.css("*::text").getall() if t.strip()]
            branch = texts[0]

            address = " ".join(caption.css("a[href*='maps.app.goo.gl']::text").getall())
            address = re.sub(r"\s+", " ", address).strip()
            street_address, _, rest = address.partition(", ")
            *_, city, state_postcode = rest.split(", ")
            state, _, postcode = state_postcode.partition(" ")

            key = self.address_key(address)
            matched_addresses.add(key)

            item = Feature()
            item["ref"] = branch
            item["branch"] = branch
            item["street_address"] = street_address
            item["city"] = city
            item["state"] = state
            item["postcode"] = postcode
            item["phone"] = caption.css("a[href^='tel:']::attr(href)").get("").removeprefix("tel:")

            if store := stores_by_address.get(key):
                item["lat"] = store["lat"]
                item["lon"] = store["lng"]

            apply_category(Categories.BANK, item)

            if "Lobby" in texts:
                oh = OpeningHours()
                oh.add_ranges_from_string(texts[texts.index("Lobby") + 1])
                item["opening_hours"] = oh

            if "Drive Up" in texts:
                drive_up_hours = OpeningHours()
                drive_up_hours.add_ranges_from_string(texts[texts.index("Drive Up") + 1])
                item["extras"]["opening_hours:drive_through"] = drive_up_hours.as_opening_hours()

            yield item

        for store in stores:
            key = self.address_key(store["address"])
            if key in matched_addresses:
                # This marker is an ATM/kiosk at a branch already yielded above.
                continue

            item = Feature()
            item["ref"] = f"{store['name']} {store['address']}"
            item["name"] = store["name"]
            item["addr_full"] = store["address"]
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]
            item["operator"] = self.item_attributes["brand"]

            apply_category(Categories.ATM, item)

            yield item
