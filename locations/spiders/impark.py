from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

BRANDS = {
    "IMP": {"brand": "Impark", "brand_wikidata": "Q6006077"},
    "CCP": {"operator": "City Center Parking", "operator_wikidata": "Q108276976"},
    "ADV": {"brand": "Advanced Parking"},
}

FEATURE_MAPPING = {
    2: "supervised",  # On-site attendant
    3: "capacity:charging",  # EV Charger
}


class ImparkSpider(Spider):
    name = "impark"
    allowed_domains = ["lots.impark.com"]

    async def start(self) -> AsyncIterator[Any]:
        for op_code in BRANDS:
            yield JsonRequest(
                url=f"https://lots.impark.com/api/lots/{op_code}/en"
                "?latLoc=0&lngLoc=0&latMin=-90&lngMin=-180&latMax=90&lngMax=180&csr=0&branchName=",
                cb_kwargs={"op_code": op_code},
            )

    def parse(self, response, op_code: str):
        for lot in response.json():
            location = lot.get("location", {})
            address = lot.get("address", {})
            branch_number = lot["branchNumber"]
            lot_number = lot["lotNumber"]

            item = Feature()
            item["ref"] = lot["lotId"]
            item["name"] = lot.get("lotName")
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["street_address"] = address.get("address1")
            item["city"] = address.get("city")
            item["state"] = address.get("provState")
            item["postcode"] = address.get("postalCode")
            item["country"] = address.get("country")
            item["website"] = f"https://lots.impark.com/imp#details={branch_number},{lot_number}"
            item.update(BRANDS[op_code])

            for feature in lot.get("features", []):
                if tag := FEATURE_MAPPING.get(feature.get("id")):
                    apply_yes_no(tag, item, True)

            apply_category(Categories.PARKING, item)
            item["extras"]["fee"] = "yes"

            yield Request(
                url=f"https://lots.impark.com/{op_code}/en/details/{branch_number}/{lot_number}?csr=0",
                headers={"x-requested-with": "XMLHttpRequest"},
                callback=self.parse_detail,
                cb_kwargs={"item": item},
            )

    def parse_detail(self, response, item: Feature):
        details = {}
        labels = response.xpath('//div[@class="detailsLotDetails"]//div[@class="lotsLabel"]/text()').getall()
        values = response.xpath('//div[@class="detailsLotDetails"]//div[@class="lotsValue"]/text()').getall()
        for label, value in zip(labels, values):
            details[label.strip().rstrip(":").strip().lower()] = value.strip()

        if capacity := details.get("number of spaces"):
            item["extras"]["capacity"] = capacity

        if lot_type := details.get("lot type"):
            lot_type_lower = lot_type.lower()
            if "below" in lot_type_lower or "underground" in lot_type_lower:
                item["extras"]["parking"] = "underground"
            elif "surface" in lot_type_lower or "flat" in lot_type_lower:
                item["extras"]["parking"] = "surface"
            elif "above" in lot_type_lower or "parkade" in lot_type_lower or "garage" in lot_type_lower:
                item["extras"]["parking"] = "multi-storey"

        if restrictions := details.get("restrictions"):
            try:
                item["opening_hours"] = self.parse_hours(restrictions)
            except Exception:
                self.logger.warning("Failed to parse hours from: %s", restrictions)

        payment_icons = response.xpath('//div[@id="dailyRate"]//span/@title').getall()
        for payment in payment_icons:
            payment_lower = payment.strip().lower()
            if payment_lower == "credit":
                apply_yes_no(PaymentMethods.CREDIT_CARDS, item, True)
            elif payment_lower == "cash":
                apply_yes_no(PaymentMethods.CASH, item, True)
            elif payment_lower == "hangtag":
                apply_yes_no(PaymentMethods.APP, item, True)

        yield item

    @staticmethod
    def parse_hours(restrictions: str) -> OpeningHours:
        oh = OpeningHours()
        restrictions_lower = restrictions.lower()
        if "24/7" in restrictions_lower or "24 hours" in restrictions_lower:
            oh.add_days_range(DAYS, "00:00", "23:59")
            return oh
        oh.add_ranges_from_string(restrictions)
        return oh
