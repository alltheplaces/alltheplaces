import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PickNPaySpider(scrapy.Spider):
    name = "pick_n_pay"
    item_attributes = {"brand": "Pick n Pay", "brand_wikidata": "Q7190735", "extras": Categories.SHOP_SUPERMARKET.value}
    start_urls = ["https://api.pnp.co.za/stores/v2"]

    def parse(self, response, **kwargs):
        for store in response.json():
            if store["storeType"] in ("ONLINE", "NO_FORMAT") or "(incomplete)" in store["storeName"].lower():
                continue
            address = store["storeAddress"]
            store.update(address)
            store["province"] = (address.get("province") or {}).get("name")
            item = DictParser.parse(store)

            item["opening_hours"] = OpeningHours()
            for day in store.get("tradingHours", []):
                # dayId is 1 to 8, 1 being Monday
                # dayId of 8 is only present on some 24/7 stores so we ignore it
                if day["dayId"] < 8:
                    item["opening_hours"].add_range(DAYS[day["dayId"] - 1], day["openTime"], day["closeTime"])

            if store["storeType"] == "HYPER":
                item.update(
                    {
                        "brand": "Pick n Pay Hyper",
                        "brand_wikidata": TODO,
                    }
                )
            if store["storeType"] == "CLOTHING":
                item.update(
                    {
                        "brand": "Pick n Pay Clothing",
                        "brand_wikidata": "Q122964352",
                        "extras": Categories.SHOP_CLOTHES.value,
                    }
                )
            elif store["storeType"] == "LIQUOR":
                item.update(
                    {
                        "brand": "Pick n Pay Liquor",
                        "brand_wikidata": "Q122764458",
                        "extras": Categories.SHOP_ALCOHOL.value,
                    }
                )
            elif store["storeType"] == in ("EXPRESS", "BPFORECOURT"):
                item.update(
                    {
                        "brand": "Pick n Pay Express",
                        "brand_wikidata": "Q122764443",
                        "extras": Categories.SHOP_CONVENIENCE.value,
                    }
                )
            elif store["storeType"] in ("BOXER", "BOXER PUNCH", "BOXER SUPERSTOR"):
                item.update(
                    {
                        "brand": "Boxer",
                        "brand_wikidata": "Q116586275",
                        "extras": Categories.SHOP_SUPERMARKET.value,
                    }
                )
            elif store["storeType"] == "BOXER LIQUOR":
                item.update(
                    {
                        "brand": "Boxer Liquors",
                        "brand_wikidata": "Q122766666",
                        "extras": Categories.SHOP_ALCOHOL.value,
                    }
                )
            elif store["storeType"] == "BOXER BUILD":
                item.update(
                    {
                        "brand": "Boxer Build",
                        "brand_wikidata": "Q122766671",
                        "extras": Categories.SHOP_DOITYOURSELF.value,
                    }
                )
            elif store["storeType"] == "DC": # Distribution Centre
                item.update(
                    {
                        "extras": Categories.INDUSTRIAL_WAREHOUSE.value,
                        "operator": "Pick n Pay",
                        "operator_wikidata": "Q7190735",
                    }
                )
            elif store["storeType"] == "REGIONAL OFFICE":
                item.update(
                    {
                        "extras": Categories.OFFICE_COMPANY.value,
                        "brand": "Pick n Pay",
                        "brand_wikidata": "Q7190735",
                    }
                )
            # Unhandled:
            # "" appears to be a data error and the single current result is a data error
            # "DAILY" was two stores, but both marked as incomplete in the data
            " "LOCAL", "MINI" appear to be branded as normal PnP supermarkets
            # "FAMILY", "SUPER" are standard PnP supermarkets
            # "MARKET" probably should be shown as PnP supermarket. Township location stores and numbers have dropped significantly recently
            # "WHOLESALE" appear to be colocated with HYPER locations
            
            yield item
