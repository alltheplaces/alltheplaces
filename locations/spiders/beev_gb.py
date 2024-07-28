from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class BeevGBSpider(Spider):
    name = "beev_gb"
    item_attributes = {"brand": "Be.EV", "brand_wikidata": "Q118263083"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://be-ev.co.uk/api/sites/GetMarkersWithFilters?ConnectorType=type2:0,ccs:0,chademo:0&ChargerType=f:0,r:0&Availability=a:0,o:0,u:0,cs:0&PaymentOptions=cless:0&AccessibilityFeatures=wpb:0,ac:0,sfk:0,sfc:0,fg:0&MultiChargerLocations=one:0,two:0,three:0,fourplus:0&SpecialistGroups=taxi:0&DifferentOperators=diffops:0&OffPeakPricing=opp:0&source=fuuse",
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["Status"] == 4:
                continue  # Upcoming

            item = Feature()
            item["ref"] = location["SiteId"]
            item["lat"] = location["Coordinates"]["Lat"]
            item["lon"] = location["Coordinates"]["Long"]
            item["name"] = location["Name"]
            item["postcode"] = location["FormattedAddress"]["PostCode"]

            apply_yes_no(Extras.FEE, item, location["Tariff"]["Amount"] == "0.00", False)
            item["extras"]["charge"] = "{} {}/kWh".format(location["Tariff"]["Amount"], location["Tariff"]["Currency"])

            apply_category(Categories.CHARGING_STATION, item)

            yield item
