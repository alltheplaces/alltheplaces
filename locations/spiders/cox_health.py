import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

LOCATION_TYPE_MAP = {
    "Clinic": Categories.CLINIC,
    "Emergency Department": Categories.EMERGENCY_WARD,
    "Facility": None,
    "Fitness Center": Categories.GYM,
    "Hospital": Categories.HOSPITAL,
    "Laboratory": Categories.MEDICAL_LABORATORY,
    "Pharmacy": Categories.PHARMACY,
    "Urgent & Walk In": Categories.CLINIC_URGENT,
}


class CoxHealthSpider(scrapy.Spider):
    name = "cox_health"
    item_attributes = {"brand": "CoxHealth", "brand_wikidata": "Q5179867"}
    start_urls = ["https://www.coxhealth.com/api/locations/"]

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["ref"] = location["uid"]
            item["street"] = None
            address = location.get("address") or {}
            item["street_address"] = ", ".join(filter(None, [address.get("street"), address.get("street2")]))
            item["lat"] = address.get("latitude")
            item["lon"] = address.get("longitude")
            item["phone"] = location.get("kyruus_phone")
            item["website"] = response.urljoin(location["uri"]) if location.get("uri") else None

            categorised = False
            for location_type in location.get("locationType") or []:
                if cat := LOCATION_TYPE_MAP.get(location_type):
                    apply_category(cat, item)
                    categorised = True
                    break
                elif location_type not in LOCATION_TYPE_MAP:
                    self.crawler.stats.inc_value(f"atp/cox_health/unmapped_category/{location_type}")

            if not categorised and "Gift" in item.get("name", ""):
                apply_category(Categories.SHOP_GIFT, item)

            yield item
