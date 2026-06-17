import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours

CATEGORY_MAP = {
    "Community Hospice": Categories.HOSPICE,
    "Diabetes Center": Categories.CLINIC,
    "Emergency Department": Categories.EMERGENCY_WARD,
    "Health Park": Categories.HOSPITAL,
    "Hospital": Categories.HOSPITAL,
    "Imaging Center": Categories.CLINIC,
    "Lab Services": Categories.MEDICAL_LABORATORY,
    "Medical Practice": Categories.DOCTOR_GP,
    "Pharmacy": Categories.PHARMACY,
    "Rehabilitation Center": Categories.REHABILITATION,
    "Senior Living": Categories.NURSING_HOME,
    "Urgent Care": Categories.CLINIC_URGENT,
    "Infusion Center": Categories.CLINIC,
    "Sleep Lab": Categories.CLINIC,
}

LISTING_PAGES = [
    "https://www.wellstar.org/locations/hospitals",
    "https://www.wellstar.org/locations/health-parks",
    "https://www.wellstar.org/locations/urgent-care-centers",
    "https://www.wellstar.org/locations/emergency-departments",
    "https://www.wellstar.org/locations/imaging-centers",
    "https://www.wellstar.org/locations/infusion-centers",
    "https://www.wellstar.org/locations/pharmacies",
    "https://www.wellstar.org/locations/rehabilitation-centers",
    "https://www.wellstar.org/locations/hospice",
    "https://www.wellstar.org/locations/lab-services",
    "https://www.wellstar.org/locations/sleep-labs",
]


class WellstarUSSpider(Spider):
    name = "wellstar_us"
    item_attributes = {"brand": "WellStar Health System", "brand_wikidata": "Q7981073"}
    allowed_domains = ["www.wellstar.org"]
    start_urls = LISTING_PAGES
    requires_proxy = "US"  # Cloudflare geoblocking in use

    def parse(self, response):
        for link in response.xpath('//a[contains(@href, "/locations/")]/@href').getall():
            parts = link.strip("/").split("/")
            if len(parts) >= 3 and parts[0] == "locations":
                yield response.follow(link, callback=self.parse_location)

    def parse_location(self, response):
        for script in response.xpath("//script/text()").getall():
            if "locationLatitude" not in script:
                continue
            for location in chompjs.parse_js_objects(script):
                if not isinstance(location, dict) or "locationLatitude" not in location:
                    continue

                item = DictParser.parse(location)
                item["lat"] = location.get("locationLatitude")
                item["lon"] = location.get("locationLongitude")
                item["phone"] = location.get("contactPhoneNumber")
                item["website"] = location.get("pageURL") or response.url

                address_data = location.get("address", "")
                address_attributes = self.get_address_attributes(address_data)
                if address_data.split(",")[0].strip():
                    item["street_address"] = address_data.split(",")[0].strip()
                    if location.get("address2"):
                        item["street_address"] = f"{item['street_address']}, {location['address2']}"
                item["city"] = address_attributes.get("city")
                item["state"] = address_attributes.get("state")
                item["postcode"] = address_attributes.get("postcode")

                item["opening_hours"] = self.parse_hours(location.get("workingHours"))

                if type_names := location.get("locationTypesNames"):
                    if cat := CATEGORY_MAP.get(type_names[0]):
                        apply_category(cat, item)

                yield item
                return

    def get_address_attributes(self, address):
        address_parts = address.split(",")
        address_attributes = {}
        if len(address_parts) > 1:
            address_attributes["city"] = address_parts[1].strip()
        if len(address_parts) > 2:
            address_attributes["state"] = address_parts[2].strip()
        if len(address_parts) > 3:
            address_attributes["postcode"] = address_parts[3].strip()

        return address_attributes

    def parse_hours(self, hours: dict | None) -> OpeningHours:
        oh = OpeningHours()
        if not hours:
            return oh
        for day_name, time_range in hours.items():
            try:
                day = DAYS_EN.get(day_name)
                if not day:
                    continue
                open_time, close_time = time_range.split("-")
                oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
            except Exception:
                continue
        return oh
