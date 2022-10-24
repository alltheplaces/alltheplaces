# -*- coding: utf-8 -*-

import scrapy
import re

from locations.items import GeojsonPointItem
from locations.user_agents import BROSWER_DEFAULT

DAYS_NAME = {
    "m": "Mo",
    "mon": "Mo",
    "t": "Tu",
    "w": "We",
    "s": "Th",
    "f": "Fr",
    "f ": "Fr",
    "sun": "Su",
    "sat": "Sa",
    "daily": "",
}


class CostcoSpider(scrapy.Spider):
    name = "costco"
    item_attributes = {"brand": "Costco", "brand_wikidata": "Q715583"}
    allowed_domains = ["www.costco.com"]
    user_agent = BROSWER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    download_delay = 0.1
    url = "https://www.costco.com/AjaxWarehouseBrowseLookupView?langId=-1&numOfWarehouses=100000&hasGas=false&hasTires=false&hasFood=false&hasHearing=false&hasPharmacy=false&hasOptical=false&hasBusiness=false&hasPhotoCenter=&tiresCheckout=0&isTransferWarehouse=false&populateWarehouseDetails=true&warehousePickupCheckout=false&latitude={lat}&longitude={lng}&countryCode=US&distance=100000"

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_50mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                yield scrapy.Request(
                    url=self.url.format(lat=lat, lng=lon),
                    callback=self.parse_ajax,
                    headers=self.headers,
                )

    def store_hours(self, store_hours):
        opening_hours = []

        if not store_hours:
            return None

        for day_info in store_hours:
            if day_info.lower().find("close") > -1:
                continue

            match = re.match(
                r"^(\w+)-?[\.:]?([A-Za-z]*)\.? *(\d{1,2}):(\d{2}) ?(am|pm|) *- +(\d{1,2}):(\d{2}) ?(am|pm|hrs\.)$",
                day_info,
            )
            if not match:
                self.logger.warn("Couldn't match hours: %s", day_info)

            try:
                (
                    day_from,
                    day_to,
                    fr_hr,
                    fr_min,
                    fr_ampm,
                    to_hr,
                    to_min,
                    to_ampm,
                ) = match.groups()
            except ValueError:
                self.logger.warn("Couldn't match hours: %s", day_info)
                raise

            day_from = DAYS_NAME[day_from.lower()]
            day_to = DAYS_NAME[day_to.lower()] if day_to else day_from

            if day_from != day_to:
                day_str = "{}-{}".format(day_from, day_to)
            else:
                day_str = "{}".format(day_from)

            day_hours = "%s %02d:%02d-%02d:%02d" % (
                day_str,
                int(fr_hr) + 12 if fr_ampm == "pm" else int(fr_hr),
                int(fr_min),
                int(to_hr) + 12 if to_ampm == "pm" else int(to_hr),
                int(to_min),
            )

            opening_hours.append(day_hours.strip())

        return "; ".join(opening_hours)

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()

    def parse_ajax(self, response):
        # If that's the case we are getting rate limited. (Even if no features are returned, it's supposed to return "[True]")
        if len(response.text) == 0:
            return

        body = response.json()

        for store in body[1:]:
            if store["distance"] < 110:
                # only process stores that are within 110 miles of query point
                # (to reduce processing a ton of duplicates)
                ref = store["identifier"]
                department = store["specialtyDepartments"]

                fuels = {}
                if "gasPrices" in store:
                    fuels = {
                        "fuel:diesel": "diesel" in store["gasPrices"],
                        "fuel:octane_87": "regular" in store["gasPrices"],
                        "fuel:octane_91": "premium" in store["gasPrices"],
                    }

                properties = {
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "ref": ref,
                    "phone": self._clean_text(store.get("phone")),
                    "name": f"Costco {store['locationName']}",
                    "street_address": store["address1"],
                    "city": store["city"],
                    "state": store["state"],
                    "postcode": store.get("zipCode"),
                    "country": store.get("country"),
                    "website": "https://www.costco.com/warehouse-locations/store-{}.html".format(
                        ref
                    ),
                    "extras": {
                        "shop": "supermarket",
                        "number": store["displayName"],
                        "amenity:fuel": store["hasGasDepartment"],
                        "amenity:pharmacy": store["hasPharmacyDepartment"],
                        "atm": any("ATM" == d["name"] for d in department) or None,
                        "fuel:propane": any("Propane" == d["name"] for d in department)
                        or None,
                        **fuels,
                    },
                }

                hours = store.get("warehouseHours")
                if hours:
                    try:
                        properties["opening_hours"] = self.store_hours(hours)
                    except:
                        pass

                yield GeojsonPointItem(**properties)
