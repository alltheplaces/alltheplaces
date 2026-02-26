import datetime
from typing import Any

from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import ITEM_PIPELINES

BRAND_MAP = {
    "ESSO": {"brand": "Esso", "brand_wikidata": "Q867662"},
    "BP": {"brand": "BP", "brand_wikidata": "Q152057"},
    "SHELL": {"brand": "Shell", "brand_wikidata": "Q110716465"},
    "TESCO": {"brand": "Tesco", "brand_wikidata": "Q487494"},
    "MORRISONS": {"brand": "Morrisons", "brand_wikidata": "Q922344"},
    "ASDA": {"brand": "Asda", "brand_wikidata": "Q297410"},
    "SAINSBURY'S": {"brand": "Sainsbury's", "brand_wikidata": "Q152096"},
    "TEXACO": {"brand": "Texaco", "brand_wikidata": "Q775060"},
    "JET": {"brand": "JET", "brand_wikidata": "Q568940"},
    "EG ON THE MOVE": {"brand": "EG On the Move", "brand_wikidata": "Q130223576"},
    "GULF": {"brand": "Gulf", "brand_wikidata": "Q5617505"},
    "Texaco": {"brand": "Texaco", "brand_wikidata": "Q775060"},
    "ASDA EXPRESS": {"brand": "Asda Express", "brand_wikidata": "Q114826023"},
    "Gulf": {"brand": "Gulf", "brand_wikidata": "Q5617505"},
    "VALERO": {"brand": "Valero", "brand_wikidata": "Q1283291"},
    "Esso": {"brand": "Esso", "brand_wikidata": "Q867662"},
    "WELCOME BREAK": {"brand": "Welcome Break", "brand_wikidata": "Q7980609"},
    "Maxol": {"brand": "Maxol", "brand_wikidata": "Q3302837"},
    "COSTCO WHOLESALE": {"brand": "Costco", "brand_wikidata": "Q715583"},
    "BP HARVEST ENERGY": {"brand": "BP", "brand_wikidata": "Q152057"},
    "Murco": {"brand": "Murco", "brand_wikidata": "Q16998281"},
    "Jet": {"brand": "JET", "brand_wikidata": "Q568940"},
    "Shell": {"brand": "Shell", "brand_wikidata": "Q110716465"},
    "TOTAL HARVEST ENERGY": {"brand": "TotalEnergies", "brand_wikidata": "Q154037"},
    "MURCO": {"brand": "Murco", "brand_wikidata": "Q16998281"},
    "CIRCLE K": {"brand": "Circle K", "brand_wikidata": "Q3268010"},
    "SHELL HARVEST ENERGY": {"brand": "Shell", "brand_wikidata": "Q110716465"},
}
FUEL_MAP = {
    "E5": "e5",
    "E10": "e10",
    # "B7P": None,
    "B7S": "diesel",
    "B10": "b10",
    "HVO": "biodiesel",
}


class GovFuelFinderGBSpider(CSVFeedSpider):
    name = "gov_fuel_finder_gb"
    start_urls = ["https://www.fuel-finder.service.gov.uk/internal/v1.0.2/csv/get-latest-fuel-prices-csv"]
    custom_settings = {
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.count_operators.CountOperatorsPipeline": None}
    }
    requires_proxy = True

    def parse_row(self, response: Response, row: dict[str, str]) -> Any:
        item = Feature()
        item["ref"] = item["extras"]["ref:GB:fuel_finder"] = row["forecourts.node_id"]
        item["lat"] = row["forecourts.location.latitude"]
        item["lon"] = row["forecourts.location.longitude"]

        if brand := BRAND_MAP.get(row["forecourts.brand_name"]):
            item.update(brand)
        else:
            item["name"] = row["forecourts.trading_name"]

        item["phone"] = row["forecourts.public_phone_number"]
        item["street_address"] = merge_address_lines(
            [row["forecourts.location.address_line_1"], row["forecourts.location.address_line_2"]]
        )
        item["city"] = row["forecourts.location.city"]
        item["postcode"] = row["forecourts.location.postcode"]

        item["extras"]["check_date"] = datetime.datetime.strptime(
            row["forecourt_update_timestamp"], "%a %b %d %Y %H:%M:%S %Z%z (Coordinated Universal Time)"
        ).strftime("%Y-%m-%d")

        apply_yes_no(Extras.CAR_WASH, item, row["forecourts.amenities.vehicle_services.car_wash"] == "true")
        apply_yes_no(Extras.TOILETS, item, row["forecourts.amenities.customer_toilets"] == "true")
        apply_yes_no(Fuel.ADBLUE, item, row["forecourts.amenities.fuel_and_energy_services.adblue_pumps"] == "true")
        apply_yes_no(
            "fuel:adblue:canister",
            item,
            row["forecourts.amenities.fuel_and_energy_services.adblue_packaged"] == "true",
        )
        apply_yes_no(Fuel.LPG, item, row["forecourts.amenities.fuel_and_energy_services.lpg_pumps"] == "true")
        # "forecourts.amenities.air_pump_or_screenwash"
        # "forecourts.amenities.water_filling"

        if row["forecourts.temporary_closure"] == "true":
            item["opening_hours"] = "closed"
        else:
            item["opening_hours"] = self.parse_opening_hours(row)

        if row["forecourts.permanent_closure"] == "true":
            set_closed(item)
        if row["forecourts.permanent_closure_date"]:
            set_closed(
                item,
                datetime.datetime.strptime(
                    row["forecourts.permanent_closure_date"],
                    "%a %b %d %Y %H:%M:%S %Z%z (Coordinated Universal Time)",
                ),
            )

        apply_category(Categories.FUEL_STATION, item)

        for key, tag in FUEL_MAP.items():
            if price := row.get("forecourts.fuel_price.{}".format(key)):
                price = float(price)
                if price < 50:
                    price *= 100
                elif price > 1000:
                    price /= 10
                item["extras"]["charge:{}".format(tag)] = "{} GBP/1 litre".format(round(price / 100, 2))
                apply_yes_no("fuel:{}".format(tag), item, True)

        yield item

    def parse_opening_hours(self, poi: dict) -> OpeningHours | str:
        if poi["forecourts.amenities.twenty_four_hour_fuel"] == "true":
            return "24/7"
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            if poi["forecourts.opening_times.usual_days.{}.is_24_hours".format(day)] == "true":
                oh.add_range(day, "00:00", "24:00")
            else:
                oh.add_range(
                    day,
                    poi["forecourts.opening_times.usual_days.{}.open_time".format(day)],
                    poi["forecourts.opening_times.usual_days.{}.close_time".format(day)],
                    "%H:%M:%S",
                )

        # "forecourts.opening_times.bank_holiday.standard.open_time"
        # "forecourts.opening_times.bank_holiday.standard.close_time"
        # "forecourts.opening_times.bank_holiday.standard.is_24_hours"

        return oh
