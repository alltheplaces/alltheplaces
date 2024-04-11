import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class KrakowPublicTransportVendingMachines(Spider):
    name = "kkm_vending_krk_pl"
    item_attributes = {"brand": "KKM", "brand_wikidata": "Q57515549"}
    start_urls = ["https://kkm.krakow.pl/pl/punkty-sprzedazy-biletow/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_raw in re.findall(r"items\.push\(\s+({.+?})\)", response.text, re.DOTALL):
            location = chompjs.parse_js_object(re.sub(r"\s:", ":", location_raw))
            item = Feature()
            item["ref"] = location["Id"]
            item["lat"] = location["Latitude"]
            item["lon"] = location["Longitude"]
            item["extras"]["location_description"] = location["Location"]
            if location["OpeningHours"] == "Całą dobę":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["OpeningHours"], DAYS_PL)

            TICKET_OFFICE_VALUES = ["2"]
            TICKET_MACHINE_WITH_INFO_KIOSK_VALUES = ["13"]
            TICKET_MACHINE_VALUES = ["1", "9"]
            TICKET_MACHINE_VALUES_WITH_NO_CACH_SUPPORT = ["41"]
            if location["TypeId"] in TICKET_OFFICE_VALUES:
                apply_category(Categories.SHOP_TICKET, item)
                item["extras"]["ticket"] = "public_transport"
                item["name"] = "Punkt Obsługi Pasażerów KMK"
                item["nsi_id"] = "N/A"
            elif location["TypeId"] in TICKET_MACHINE_WITH_INFO_KIOSK_VALUES + TICKET_MACHINE_VALUES:
                item["extras"]["payment:cash"] = "yes"
                item["extras"]["payment:cards"] = "yes"
            elif location["TypeId"] in TICKET_MACHINE_VALUES_WITH_NO_CACH_SUPPORT:
                item["extras"]["payment:cash"] = "no"
                item["extras"]["payment:cards"] = "yes"
            else:
                self.crawler.stats.inc_value("atp/kkm_vending_krk_pl/unmapped_type/{}".format(location["TypeId"]))
                continue

            yield item
