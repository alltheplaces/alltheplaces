from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

SHOPRITE_BRANDS = {
    "Checkers": {"brand": "Checkers", "brand_wikidata": "Q5089126", "category": Categories.SHOP_SUPERMARKET},
    "Checkers Hyper": {
        "brand": "Checkers Hyper",
        "brand_wikidata": "Q116518886",
        "category": Categories.SHOP_SUPERMARKET,
    },
    "Checkers LiquorShop": {
        "brand": "Checkers",
        "brand_wikidata": "Q5089126",
        "category": Categories.SHOP_ALCOHOL,
    },
    "MediRite": {
        "brand": "MediRite",
        "brand_wikidata": "Q115696233",
        "located_in": "Checkers",
        "located_in_wikidata": "Q5089126",
        "category": Categories.PHARMACY,
    },
    "MediRite Plus": {"brand": "MediRite Plus", "brand_wikidata": "Q115696233", "category": Categories.PHARMACY},
    "Shoprite": {"brand": "Shoprite", "brand_wikidata": "Q1857639", "category": Categories.SHOP_SUPERMARKET},
    "Shoprite Hyper": {
        "brand": "Shoprite Hyper",
        "brand_wikidata": "Q1857639",
        "category": Categories.SHOP_SUPERMARKET,
    },
    "Shoprite LiquorShop": {
        "brand": "LiquorShop Shoprite",
        "brand_wikidata": "Q1857639",
        "category": Categories.SHOP_ALCOHOL,
    },
    "Shoprite Mini": {
        "brand": "Shoprite Mini",
        "brand_wikidata": "Q1857639",
        "category": Categories.SHOP_CONVENIENCE,
    },
    "Super Usave": {
        "brand": "Super Usave",
        "brand_wikidata": "Q115696368",
        "category": Categories.SHOP_SUPERMARKET,
    },
    "Usave": {"brand": "Usave", "brand_wikidata": "Q115696368", "category": Categories.SHOP_SUPERMARKET},
}

COUNTRY_IDS = {
    "7": "AO",
    "29": "BW",
    "83": "GH",
    "121": "LS",
    "130": "MW",
    "147": "MZ",
    "149": "NA",
    "205": "SZ",
    "198": "ZA",
    "239": "ZM",
}

STORES_API = "https://www.medirite.co.za/bin/commons/stores.json"


class ShopriteHoldingsSpider(Spider):
    name = "shoprite_holdings"
    brand_filters = [
        "Medirite",  # Gets Checkers, Checkers Hyper, Checkers LiquorShop, MediRite, MediRite Plus
        "Shoprite",  # Gets Shoprite, Shoprite LiquorShop, Usave, Shoprite Mini
    ]

    start_urls = [
        f"{STORES_API}?national=yes&brand={brand}&country={country}"
        for brand in brand_filters
        for country in COUNTRY_IDS
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_store_list)

    def parse_store_list(self, response: Response) -> Iterable[JsonRequest]:
        store_list = response.json()
        if not isinstance(store_list, dict):
            # A brand/country pair with no stores returns a bare status list, e.g. [204]
            return

        for location in store_list["stores"]:
            location["ref"] = location.pop("uid")

            location = {k: v for k, v in location.items() if v not in ("null", "")}

            if location.get("phoneInternationalCode") and location.get("phoneNumber"):
                location["phoneNumber"] = (
                    "+"
                    + location["phoneInternationalCode"].removeprefix("00")
                    + " "
                    + location["phoneNumber"].lstrip("0")
                )

            location["street-address"] = clean_address(
                [location.get("physicalAdd1"), location.get("physicalAdd2"), location.get("physicalAdd3")]
            )
            location["province"] = location.get("physicalProvince")

            # Placeholder postcodes (9000 is used for many NA locations, but is not a valid postcode in NA)
            if location.get("postalCode") in ["0000", "00000", "9000"]:
                location.pop("postalCode")

            item = DictParser.parse(location)

            item["branch"] = location["branch"]
            attributes = dict(SHOPRITE_BRANDS[location["brand"]])
            apply_category(attributes.pop("category"), item)
            item.update(attributes)
            item["website"] = self.get_website(item)

            yield JsonRequest(
                url=f"{STORES_API}?uid={item['ref']}",
                meta={"item": item},
                callback=self.parse_store,
            )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        # response.json()["singleStoreData"][0] repeats the main stores.json record, so it is ignored

        services = [service["FacilityTypeName"] for service in response.json()["services"]]
        # Many other services can be listed for Checkers and LiquorShop, but not all refer to in-store facilities, some are just available nearby
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Friendly" in services)
        apply_yes_no(Extras.DELIVERY, item, "Sixty60 Online Grocery Delivery" in services)

        item["opening_hours"] = OpeningHours()
        for day_hours in response.json()["times"]:
            # Values greater than 1 appear to be for single-data closures, e.g. holidays
            if day_hours["TradingTimeTypeID"] != 1:
                continue
            if day_hours["IsClosed"]:
                item["opening_hours"].set_closed(day_hours["TradingDay"])
            else:
                item["opening_hours"].add_range(day_hours["TradingDay"], day_hours["StartTime"], day_hours["EndTime"])

        item["extras"]["@source_uri"] = f"{STORES_API}?uid={item['ref']}"
        yield item

    def get_website(self, item: Feature) -> str | None:
        # Checkers/Shoprite ZA redirect to fuller urls, but this seems simpler
        # e.g. https://www.shoprite.co.za/Western-Cape/Cape-Town/Durbanville/Shoprite-Durbanville/store-details/1894
        # i.e. /province/city/suburb/brand-branch/ref
        if item.get("brand") == "Checkers" and item.get("country") == "South Africa":
            return "https://www.checkers.co.za/store-details/" + item["ref"]
        if item.get("brand") == "Shoprite" and item.get("country") == "South Africa":
            return "https://www.shoprite.co.za/store-details/" + item["ref"]
        if item.get("brand") == "Shoprite" and item.get("country") == "Namibia":
            return f"https://www.shoprite.com.na/store-locator.html?u={item['ref']}&b=Shoprite&c=149"
        return None
