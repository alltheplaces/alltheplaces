import io
from typing import Any

from openpyxl import load_workbook
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.alior_bank_pl import AliorBankPLSpider
from locations.spiders.millennium_bank_pl import MillenniumBankPLSpider
from locations.spiders.santander_pl import SantanderPLSpider

BRAND_MAPPING = {
    "Alior Bank Poland ADT Recycler": {
        "brand": AliorBankPLSpider.item_attributes["brand"],
        "brand_wikidata": AliorBankPLSpider.item_attributes["brand_wikidata"],
        "operator": AliorBankPLSpider.item_attributes["brand"],
        "operator:wikidata": AliorBankPLSpider.item_attributes["brand_wikidata"],
    },
    "Bank Millennium Poland ADT Recycler": {
        "brand": MillenniumBankPLSpider.item_attributes["brand"],
        "brand_wikidata": MillenniumBankPLSpider.item_attributes["brand_wikidata"],
        "operator": MillenniumBankPLSpider.item_attributes["brand"],
        "operator:wikidata": MillenniumBankPLSpider.item_attributes["brand_wikidata"],
    },
    "Euronet Poland ADT Recycler": {
        "brand": "Euronet",
        "brand_wikidata": "Q5412010",
        "operator": "Euronet",
        "operator:wikidata": "Q5412010",
    },
    "mBank Poland ADT Recycler": {
        "brand": "mBank",
        "brand_wikidata": "Q1160928",
        "operator": "mBank",
        "operator:wikidata": "Q1160928",
    },
    "Santander Bank Poland ADT Dual": {
        "brand": SantanderPLSpider.item_attributes["brand"],
        "brand_wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
        "operator": SantanderPLSpider.item_attributes["brand"],
        "operator:wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
    },
    "Santander Bank Poland ADT Recycler": {
        "brand": SantanderPLSpider.item_attributes["brand"],
        "brand_wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
        "operator": SantanderPLSpider.item_attributes["brand"],
        "operator:wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
    },
    "Santander Bank Poland Off-Branch ADT Dual": {
        "brand": SantanderPLSpider.item_attributes["brand"],
        "brand_wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
        "operator": SantanderPLSpider.item_attributes["brand"],
        "operator:wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
    },
    "Santander Bank Poland Off-Branch ADT Recycler": {
        "brand": SantanderPLSpider.item_attributes["brand"],
        "brand_wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
        "operator": SantanderPLSpider.item_attributes["brand"],
        "operator:wikidata": SantanderPLSpider.item_attributes["brand_wikidata"],
    },
    "SKOK Stefczyka Poland ADT Recycler": {
        "brand": "SKOK Stefczyka",
        "brand_wikidata": "Q57624461",
        "operator": "SKOK Stefczyka",
        "operator:wikidata": "Q57624461",
    },
}


def parse_hours(hours_str: str) -> str | OpeningHours | None:
    """Parse hours like '00:00-23:59' into OpeningHours format"""
    if not hours_str or hours_str == "24/7":
        return "24/7"

    try:
        oh = OpeningHours()
        # Format appears to be HH:MM-HH:MM for all days
        if "-" in hours_str:
            start, end = hours_str.split("-")
            oh.add_days_range(DAYS, start.strip(), end.strip())
        return oh
    except:
        # If parsing fails, return None
        return None


class EuronetPLSpider(Spider):
    name = "euronet_pl"
    item_attributes = {"network": "Euronet", "network_wikidata": "Q5412010"}
    start_urls = ["https://euronet.pl/Lista_wplatomatow_sieci_Euronet.xlsx"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        excel_file = response.body
        excel_data = io.BytesIO(excel_file)
        workbook = load_workbook(excel_data, read_only=True)
        sheet = workbook.active

        data = []
        for row in sheet.iter_rows(values_only=True):
            data.append(row)

        headers = data[0]
        json_data = []
        for row in data[1:]:
            json_data.append({headers[i]: cell for i, cell in enumerate(row)})

        for location in json_data:
            # Skip non-live locations
            if location.get("Status") != "Live":
                continue

            item = Feature()

            # Reference ID
            item["ref"] = location.get("ID")

            # Brand from the Brand column with mapping
            if raw_brand := location.get("Brand"):
                if brand_info := BRAND_MAPPING.get(raw_brand):
                    item.update(brand_info)
                else:
                    # Fallback to raw brand if not in mapping
                    item["brand"] = raw_brand

            # Extract coordinates (replace comma with period for decimal separator)
            if lat := location.get("GPS_Latitude"):
                item["lat"] = str(lat).replace(",", ".")
            if lon := location.get("GPS_Longitude"):
                item["lon"] = str(lon).replace(",", ".")

            # Address fields
            item["street_address"] = location.get("Address")
            item["city"] = location.get("City")
            item["postcode"] = location.get("Post code")
            item["state"] = location.get("District")

            # Name/location description
            item["name"] = location.get("Name")

            # Opening date from Live Date column
            if live_date := location.get("Live Date"):
                item["extras"]["start_date"] = live_date.strftime("%Y-%m-%d")

            # Opening hours
            if hours := location.get("Client access hours"):
                item["opening_hours"] = parse_hours(hours)

            # Apply ATM category
            apply_category(Categories.ATM, item)

            yield item
