from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

PAYMENT_MAPPING = {
    "CASH": PaymentMethods.CASH,
    "HAVE_TERMINAL": PaymentMethods.CARDS,
    "HAVE_CASHLESS": None,
}


class SdekSpider(scrapy.Spider):
    name = "sdek"
    allowed_domains = ["www.cdek.ru"]
    start_urls = ["https://www.cdek.ru/api-site/website/office/map/?websiteId=ru&locale=ru"]
    item_attributes = {"brand": "СДЭК", "brand_wikidata": "Q28665980", "extras": {"brand:en": "SDEK"}}
    requires_proxy = True

    def parse(self, response):
        data = response.json()
        for poi in data.get("data", {}).get("data", []):
            yield JsonRequest(
                "https://www.cdek.ru/api-site/v1/graphql/", data=self.graphql_query(poi["id"]), callback=self.parse_poi
            )

    def parse_poi(self, response):
        data = response.json()
        poi = data.get("data", {}).get("websiteOffice")
        item = DictParser.parse(poi)
        item["street_address"] = item.pop("addr_full")
        item["ref"] = poi.get("code")
        item["website"] = urljoin("https://www.cdek.ru", poi.get("pathForWebView"))
        item["phone"] = "; ".join(poi.get("contactPhone"))
        item["email"] = "; ".join(poi.get("contactEmail"))
        item["lat"] = poi.get("geoLatitude")
        item["lon"] = poi.get("geoLongitude")

        category = poi.get("type")
        if category == "PVZ":
            apply_category(Categories.POST_OFFICE, item)
        elif category == "POSTAMAT":
            apply_category(Categories.PARCEL_LOCKER, item)
            apply_yes_no("parcel_mail_in", item, poi.get("isReception"))
            apply_yes_no("parcel_pickup", item, poi.get("isHangout"))
        self.parse_hours(item, poi)
        self.parse_payment(item, poi)
        yield item

    def parse_hours(self, item, poi):
        if hours := poi.get("worktimes"):
            try:
                oh = OpeningHours()
                for hour in hours:
                    oh.add_range(
                        day=DAYS[hour["day"] - 1],
                        open_time=hour["startTime"],
                        close_time=hour["stopTime"],
                        time_format="%H:%M:%S",
                    )
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours: {hours}, {e}")

    def parse_payment(self, item, poi):
        if payments := poi.get("payments"):
            for payment in payments:
                if tag := PAYMENT_MAPPING.get(payment):
                    apply_yes_no(tag, item, True)

    def graphql_query(self, poi_id):
        return {
            "query": """query websiteOffice(
            $id: UID!
            ) {
            websiteOffice(id: $id)
            {
                id
                type
                name
                city
                active
                contactPhone
                contactEmail
                payments
                isReception
                isHangout
                holidays {
                    dateBegin
                    dateEnd
                }
                shorterDays {
                    dateBegin
                    dateEnd
                    timeBegin
                    timeEnd
                }
                maxDimensions {
                depth
                height
                width
                }
                metroStations {
                name
                line {
                    name
                    color
                }
                }
                geoLatitude
                geoLongitude
                weight {
                    weightMin
                    weightMax
                }
                worktime
                worktimes {
                    day
                    startTime
                    stopTime
                }
                code
                address
                pathForWebView
                dimensions {
                depth
                height
                width
                }
                timezone
            }
            }""",
            "variables": {"id": int(poi_id)},
        }
