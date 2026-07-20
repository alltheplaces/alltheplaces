from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class PickNPaySpider(Spider):
    name = "pick_n_pay"
    start_urls = ["https://api.pnp.co.za/stores/v2"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            if (
                store["storeType"] in ("", "ONLINE", "NO_FORMAT", "WHOLESALE")
                or "(incomplete)" in (store["storeName"] or "").lower()
            ):
                # "" appears to be a data error and the single current result is a data error
                # "WHOLESALE" appear to be colocated with HYPER locations, so is probably not a distinct store
                continue
            address = store["storeAddress"]
            address["province"] = (address.get("province") or {}).get("name")
            store.update(address)
            item = DictParser.parse(store)

            if item.get("name"):
                item["branch"] = (
                    item.pop("name")
                    .removeprefix("Boxer ")
                    .removeprefix("BP @ ")
                    .removeprefix("BP ")
                    .removeprefix("Clothing ")
                    .removeprefix("PnP ")
                    .removeprefix("PnP")
                )

            # Multiple phone numbers are entered like "016 362 3760/1/2"
            if item.get("phone") and "/" in item.get("phone"):
                phone_parts = [part.strip() for part in item["phone"].split("/")]
                base_number = phone_parts[0]

                results = [base_number]

                for part in phone_parts[1:]:
                    part = part.strip()
                    full_number = f"{base_number[:-len(part)]}{part}"
                    results.append(full_number)

                item["phone"] = "; ".join(results)

            item["opening_hours"] = OpeningHours()
            for day in store.get("tradingHours", []):
                # dayId is 1 to 8, 1 being Monday
                # dayId of 8 is only present on some 24/7 stores so we ignore it
                if day["dayId"] < 8:
                    item["opening_hours"].add_range(DAYS[day["dayId"] - 1], day["openTime"], day["closeTime"])

            if store["storeType"] in ("LOCAL", "MINI", "FAMILY", "SUPER", "MARKET"):
                # "LOCAL", "MINI" appear to be branded as normal PnP supermarkets
                # "FAMILY", "SUPER" are standard PnP supermarkets
                # "MARKET" probably should be shown as PnP supermarket. Township location stores and numbers have dropped significantly in recent years
                item.update({"brand": "Pick n Pay", "brand_wikidata": "Q7190735"})
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif store["storeType"] == "HYPER":
                item.update({"brand": "Pick n Pay Hyper", "brand_wikidata": "Q128791977"})
            elif store["storeType"] == "CLOTHING":
                item.update({"brand": "Pick n Pay Clothing", "brand_wikidata": "Q122964352"})
                apply_category(Categories.SHOP_CLOTHES, item)
            elif store["storeType"] == "LIQUOR":
                item.update({"brand": "Pick n Pay Liquor", "brand_wikidata": "Q122764458"})
                apply_category(Categories.SHOP_ALCOHOL, item)
            elif store["storeType"] in ("EXPRESS", "BPFORECOURT"):
                item.update({"brand": "Pick n Pay Express", "brand_wikidata": "Q122764443"})
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif store["storeType"] in ("BOXER", "BOXER PUNCH", "BOXER SUPERSTOR"):
                item.update({"brand": "Boxer", "brand_wikidata": "Q116586275"})
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif store["storeType"] == "BOXER LIQUOR":
                item.update({"brand": "Boxer Liquors", "brand_wikidata": "Q122766666"})
                apply_category(Categories.SHOP_ALCOHOL, item)
            elif store["storeType"] == "BOXER BUILD":
                item.update({"brand": "Boxer Build", "brand_wikidata": "Q122766671"})
                apply_category(Categories.SHOP_DOITYOURSELF, item)
            elif store["storeType"] == "DC":  # Distribution Centre
                item.update({"operator": "Pick n Pay", "operator_wikidata": "Q7190735"})
                apply_category(Categories.INDUSTRIAL_WAREHOUSE, item)
            elif store["storeType"] == "REGIONAL OFFICE":
                item.update({"brand": "Pick n Pay", "brand_wikidata": "Q7190735"})
                apply_category(Categories.OFFICE_COMPANY, item)
            else:
                item.update({"brand": "Pick n Pay", "brand_wikidata": "Q7190735"})
                apply_category(Categories.SHOP_SUPERMARKET, item)
            # Unhandled:
            # "DAILY" was two stores, but both marked as incomplete in the data

            yield item
