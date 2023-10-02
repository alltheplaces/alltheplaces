import string

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class MorrisonsSpider(Spider):
    name = "morrisons_gb"
    item_attributes = {"nsi_id": -1}  # Skip NSI matching as it
    # conflates stores and
    # fuel stations.
    allowed_domains = ["api.morrisons.com"]
    start_urls = ["https://api.morrisons.com/location/v2//stores?apikey=kxBdM2chFwZjNvG2PwnSn3sj6C53dLEY&limit=20000"]

    MARTINS = {
        "brand": "Martin's",
        "brand_wikidata": "Q116779207",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }

    MCCOLLS = {
        "brand": "McColl's",
        "brand_wikidata": "Q16997477",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }

    MORRISONS_FUEL_STATION = {
        "brand": "Morrisons",
        "brand_wikidata": "Q922344",
        "extras": Categories.FUEL_STATION.value,
    }

    MORRISONS_SUPERMARKET = {
        "brand": "Morrisons",
        "brand_wikidata": "Q922344",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }

    MORRISONS_DAILY_CONVENIENCE = {
        "brand": "Morrisons Daily",
        "brand_wikidata": "Q99752411",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }

    MORRISONS_DAILY_FUEL_STATION = {
        "brand": "Morrisons Daily",
        "brand_wikidata": "Q99752411",
        "extras": Categories.FUEL_STATION.value,
    }

    MORRISONS_SELECT = {
        "brand": "Morrisons Select",
        "brand_wikidata": "Q105221633",
        "extras": Categories.FUEL_STATION.value,
    }

    RS_MCCOLL = {
        "brand": "RS McColl",
        "brand_wikidata": "Q7277785",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["name"]
            item["name"] = location["storeName"]
            item["street_address"] = ", ".join(
                filter(None, [location["address"].get("addressLine1"), location["address"].get("addressLine2")])
            )
            item["website"] = (
                "https://my.morrisons.com/storefinder/"
                + str(location["name"])
                + "/"
                + location["storeName"].lower().translate(str.maketrans("", "", string.punctuation)).replace(" ", "-")
            )

            item["opening_hours"] = OpeningHours()
            for day_abbrev, day_hours in location["openingTimes"].items():
                item["opening_hours"].add_range(
                    DAYS_EN[day_abbrev.title()], day_hours["open"], day_hours["close"], "%H:%M:%S"
                )

            if location["storeFormat"] == "supermarket" and location["category"] == "Supermarket":
                item.update(self.MORRISONS_SUPERMARKET)
            elif location["storeFormat"] == "supermarket" and location["category"] == "McColls":
                if "Morrisons Daily" in location["storeName"]:
                    item.update(self.MORRISONS_DAILY_CONVENIENCE)
                elif "McColl's" in location["storeName"]:
                    item.update(self.MCCOLLS)
                elif "Rs Mccoll" in location["storeName"]:
                    item.update(self.RS_MCCOLL)
            elif location["storeFormat"] == "supermarket" and location["category"] == "Gas Station":
                if "Morrisons Daily" in location["storeName"]:
                    item.update(self.MORRISONS_DAILY_FUEL_STATION)
                elif "Morrisons Select" in location["storeName"]:
                    item.update(self.MORRISONS_SELECT)
            elif location["storeFormat"] == "pfs" and location["category"] == "Gas Station":
                item.update(self.MORRISONS_FUEL_STATION)

            if not item.get("brand"):
                continue

            yield item
