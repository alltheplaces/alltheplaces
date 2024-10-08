from scrapy import Request
from scrapy.http import FormRequest

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_ES
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider

FEATURES_EXTRAS_MAP = {
    "drivethru": Extras.DRIVE_THROUGH,
    "walkup": None,
    "tasteefreez": Extras.ICE_CREAM,
    "diningroom": Extras.INDOOR_SEATING,
    "patio": Extras.OUTDOOR_SEATING,
    "breakfast": Extras.BREAKFAST,
    "takeout": Extras.TAKEAWAY,
}


class WienerschnitzelUSECSpider(StoreLocatorPlusSelfSpider):
    name = "wienerschnitzel_us_ec"
    item_attributes = {
        "brand_wikidata": "Q324679",
        "brand": "Wienerschnitzel",
    }
    allowed_domains = ["www.wienerschnitzel.com", "wienerschnitzel.ec"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    max_results = 10000
    search_radius = 30000

    def start_requests(self):
        url = f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php"
        formdata = {
            "action": "csl_ajax_onload",
            "lat": "0",
            "lng": "0",
            "radius": str(self.search_radius),
            "options[initial_results_returned]": str(self.max_results),
            "options[distance_unit]": "kilometers",
        }
        yield FormRequest(url=url, formdata=formdata, method="POST")

    def parse_item(self, item, location, **kwargs):
        item["branch"] = item.pop("name")
        yield Request(item["website"], callback=self.parse_store_page, cb_kwargs={"item": item})

    def parse_store_page(self, response, item):
        MicrodataParser.convert_to_json_ld(response)
        ld = next(LinkedDataParser.iter_linked_data(response, "json"))

        # Fix Spanish day names
        if spec := ld.get("openingHoursSpecification"):
            if isinstance(spec, list):
                for rule in spec:
                    if not isinstance(rule, dict):
                        continue
                    if day_of_week := rule.get("dayOfWeek"):
                        if isinstance(day_of_week, list):
                            for i, day in enumerate(day_of_week):
                                day_of_week[i] = DAYS_ES.get(day, day)

        item["opening_hours"] = LinkedDataParser.parse_opening_hours(ld)

        for feature_class in response.xpath("//div[@class='location-features']/div/@class"):
            feature, has = feature_class.get().split()
            extra = FEATURES_EXTRAS_MAP[feature]
            if extra is not None:
                apply_yes_no(extra, item, has == "yes")

        item["image"] = response.xpath("//div[starts-with(@class, 'streetview-thumb')]/img/@src").get()

        yield item
