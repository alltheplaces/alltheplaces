# -*- coding: utf-8 -*-
import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.geo import postal_regions


class CostaCoffeeGBSpider(scrapy.Spider):
    name = "costacoffee_gb"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    download_delay = 1.0
    # Do our own de-duping as so common!
    my_ids = []

    def start_requests(self):
        # Costa API only returns very local results and hence requires a rather heavy approach.
        template = "https://www.costa.co.uk/api/locations/stores?latitude={}&longitude={}&maxrec=500"
        for point in postal_regions("GB"):
            url = template.format(point["latitude"], point["longitude"])
            yield scrapy.http.Request(url)

    def parse(self, response):
        def is_express(s):
            return s.get("storeType") == "COSTA EXPRESS"

        for store in response.json()["stores"]:
            if not store.get("storeStatus") == "TRADING":
                continue
            store.update(store["storeAddress"])
            item = DictParser.parse(store)

            item["ref"] = store["storeNo8Digit"]
            if item["ref"] in self.my_ids:
                continue
            self.my_ids.append(item["ref"])

            item["name"] = store["storeNameExternal"]
            if is_express(store):
                item["name"] = "Costa Coffee (Express)"

            oh = OpeningHours()
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if store["storeOperatingHours"]["open" + day] != "":
                    oh.add_range(
                        day[0:2],
                        store["storeOperatingHours"]["open" + day],
                        store["storeOperatingHours"]["close" + day],
                    )
            item["opening_hours"] = oh.as_opening_hours()

            extras = item["extras"] = {}
            for sf in store["storeFacilities"]:

                def yes_or_no(condition):
                    return "yes" if condition else "no"

                if sf["name"] == "Wifi":
                    if sf["active"]:
                        extras["internet_access"] = "wlan"
                    else:
                        extras["internet_access"] = "no"
                elif sf["name"] == "Disabled WC":
                    if sf["active"]:
                        extras["toilets"] = "yes"
                        extras["toilets:wheelchair"] = "yes"
                    else:
                        extras["toilets:wheelchair"] = "no"
                elif sf["name"] == "Baby Changing":
                    extras["changing_table"] = yes_or_no(sf["active"])
                elif sf["name"] == "Disabled Access":
                    extras["wheelchair"] = yes_or_no(sf["active"])
                elif sf["name"] == "Drive Thru":
                    extras["drive_through"] = yes_or_no(sf["active"])
                elif sf["name"] == "Delivery":
                    extras["delivery"] = yes_or_no(sf["active"])

            yield item

    # TODO: checked in this unused code as a reminder that a structural solution is needed on the branding
    @staticmethod
    def check_for_location(store):
        ns = store["storeNameExternal"]
        nsl = ns.lower()

        if "morrisons" in nsl and "PFS" in ns:
            return "Brand.MORRISONS / FUEL"

        if "sainsbury" in nsl and "PFS" in ns:
            return "Brand.SAINSBURYS / FUEL"

        if "sainsbury" in nsl and "local" in nsl:
            return "Brand.SAINSBURYS_LOCAL / FUEL"

        if "tesco" in nsl and "PFS" in ns:
            return "Brand.TESCO / FUEL"

        if "tesco" in nsl:
            return "Brand.TESCO"

        if "scotmid" in nsl:
            return "Brand.SCOTMID"

        # There are quite a few ways of spelling Co-Op!
        for s in ["co op", "coop", "co-op", "central england co"]:
            if s in nsl:
                return "Brand.COOP_UK"

        if "next " in nsl:
            return "Brand.NEXT"

        if "one stop" in nsl:
            return "Brand.ONE_STOP"

        if "spar " in nsl:
            return "Brand.SPAR"

        if "nisa @ " in nsl or "nisa local" in nsl or "@ nisa " in nsl:
            return "Brand.NISA_LOCAL"

        if "@ budgens" in nsl:
            return "Brand.BUDGENS"

        if "@ londis" in nsl:
            return "Brand.LONDIS"

        if "shell uk" in nsl:
            return "Brand.SHELL"

    # TODO: leaving this old code lying around as a reminder that a more structural solution is needed.
    @staticmethod
    def dead_code(item, store):
        addr_full = ", ".join(
            filter(
                None,
                (
                    store["addressLine1"],
                    store["addressLine2"],
                    store["addressLine3"],
                    store["city"],
                    store["postCode"],
                    "United Kingdom",
                ),
            ),
        )
        item["addr_full"] = addr_full.strip()
