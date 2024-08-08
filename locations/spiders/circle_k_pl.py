import json
from typing import Any

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

FUELS_MAP = {
    "EU_ADBLUE": Fuel.ADBLUE,
    "EU_BENZIN_95": Fuel.OCTANE_95,
    "EU_DIESEL": Fuel.DIESEL,
    "EU_LPG": Fuel.LPG,
    "EU_MILESPLUS_95": Fuel.OCTANE_95,
    "EU_MILESPLUS_98": Fuel.OCTANE_98,
    "EU_MILESPLUS_DIESEL": Fuel.DIESEL,
    "EU_MILES_95": Fuel.OCTANE_95,
    "EU_MILES_98": Fuel.OCTANE_98,
    "EU_MILES_DIESEL": Fuel.DIESEL,
    "EU_SUPRAGAZ": Fuel.LPG,
}


@staticmethod
def parse_opening_hours(times: dict, key: str) -> str | None | OpeningHours:
    if times["alwaysOpen"]:
        return "24/7"
    if not times[key]:
        return None
    oh = OpeningHours()
    oh.add_days_range(DAYS[0:4], times[key]["weekdays"]["open"], times[key]["weekdays"]["close"])
    oh.add_range(DAYS[5], times[key]["saturday"]["open"], times[key]["saturday"]["close"])
    oh.add_range(DAYS[6], times[key]["sunday"]["open"], times[key]["sunday"]["close"])

    return oh


class CircleKPLSpider(Spider):
    name = "circle_k_pl"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.pl/wyszukaj-stacje"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.xpath('//script[@data-drupal-selector="drupal-settings-json"]/text()').get())

        for location in data["ck_sim_search"]["station_results"].values():
            if location["/sites/{siteId}"]["status"] != "Active":
                continue
            item = Feature()
            item["ref"] = str(location["/sites/{siteId}"]["id"])
            item["lat"] = location["/sites/{siteId}/location"]["lat"]
            item["lon"] = location["/sites/{siteId}/location"]["lng"]
            item["street_address"] = location["/sites/{siteId}/addresses"]["PHYSICAL"]["street"]
            item["city"] = location["/sites/{siteId}/addresses"]["PHYSICAL"]["city"]
            item["state"] = location["/sites/{siteId}/addresses"]["PHYSICAL"]["state"]
            item["postcode"] = location["/sites/{siteId}/addresses"]["PHYSICAL"]["postalCode"]
            item["country"] = location["/sites/{siteId}/addresses"]["PHYSICAL"]["country"]
            item["operator"] = location["/sites/{siteId}/business-info"]["companyName"]

            if phones := location["/sites/{siteId}/contact-details"]["phones"]:
                item["phone"] = phones.get("WOR")
                item["extras"]["fax"] = phones.get("FAX")

            if emails := location["/sites/{siteId}/contact-details"]["emails"]:
                item["email"] = "; ".join(emails["DN"])

            services = [s["name"] if s["state"] == "ENABLED" else None for s in location["/sites/{siteId}/services"]]
            apply_yes_no(Extras.WHEELCHAIR, item, "EU_ACCESSIBLE_FACILITIES" in services)
            apply_yes_no(Extras.ATM, item, "EU_ATM" in services)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "EU_BABY_CHANGING" in services)
            apply_yes_no(Extras.CAR_WASH, item, "EU_CARWASH" in services or "EU_CARWASH_JETWASH" in services)
            apply_yes_no("sells:lottery", item, "EU_LOTTO" in services)
            apply_yes_no(Extras.SELF_CHECKOUT, item, "EU_SELF_CHECKOUT" in services)
            apply_yes_no(Extras.SHOWERS, item, "EU_SHOWER" in services)
            apply_yes_no(Extras.TOILETS, item, "EU_TOILETS_BOTH" in services)
            apply_yes_no(Extras.WIFI, item, "EU_WIFI" in services)

            shop = None
            if location["/sites/{siteId}/business-info"]["chainConvenience"]:
                shop = item.deepcopy()
                shop["ref"] += "-shop"
                apply_category(Categories.SHOP_CONVENIENCE, shop)
                shop["opening_hours"] = parse_opening_hours(
                    location["/sites/{siteId}/opening-info"], "openingTimesStore"
                )

            apply_category(Categories.FUEL_STATION, item)
            item["opening_hours"] = parse_opening_hours(location["/sites/{siteId}/opening-info"], "openingTimesFuel")

            for fuel in location["/sites/{siteId}/fuels"]:
                if fuel["name"] not in FUELS_MAP:
                    self.crawler.stats.inc_value(
                        "atp/circle_k_pl/fuels_map/missing/{}/{}".format(fuel["name"], fuel["displayName"])
                    )
                if fuel := FUELS_MAP.get(fuel["name"]):
                    apply_yes_no(fuel, item, True)

            # Follow redirect to collect real url
            yield Request(
                "https://www.circlek.pl/station/{}".format(item["ref"]),
                callback=self.parse_webpage,
                cb_kwargs={"fuel": item, "shop": shop},
            )

    def parse_webpage(self, response: Response, fuel: Feature, shop: Feature, **kwargs: Any) -> Any:
        fuel["website"] = response.url
        yield fuel
        if shop:
            shop["website"] = response.url
            yield shop
