from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class DorevitchPathologyAUSpider(Spider):
    name = "dorevitch_pathology_au"
    item_attributes = {
        "brand": "Dorevitch Pathology",
        "brand_wikidata": "Q126165490",
        "extras": Categories.SAMPLE_COLLECTION.value,
    }
    start_urls = ["https://locations.healius.com.au/structr/rest/Location/fetchLocationFromFindUsAPI"]
    company_code = "dorevitch"
    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt doesn't exist, ignore to avoid warnings.

    def start_requests(self):
        data = {
            "companyCode": self.company_code,
            "all": True,
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST", callback=self.parse)

    def parse(self, response):
        for location in response.json()["result"]:
            item = DictParser.parse(location)
            item["ref"] = location.get("ccId", location.get("id"))
            item["addr_full"] = clean_address([location.get("address"), location.get("address2")])
            item["street_address"] = location.get("address")
            item["opening_hours"] = self.parse_hours(location)

            # Known facilities are "toilet", "parking" and "wheelchair".
            facilities = [x["icon"] for x in location.get("facilities", [])]
            apply_yes_no(Extras.TOILETS, item, "toilet" in facilities, False)
            apply_yes_no(Extras.WHEELCHAIR, item, "wheelChair" in facilities, False)

            yield item

    @staticmethod
    def parse_hours(feature: dict) -> OpeningHours:
        hours_string = ""
        day_pairs = [
            ["Monday", "Tuesday"],
            ["Tuesday", "Wednesday"],
            ["Wednesday", "Thursday"],
            ["Thursday", "Friday"],
            ["Friday", "Saturday"],
            ["Saturday", "Sunday"],
            ["Sunday", "Monday"],
        ]
        for day_hours in feature.get("days", []):
            day_name = day_hours["day"].split(" ", 1)[0]
            hours_string = f"{hours_string} {day_name}: "
            for shift in day_hours.get("shifts", []):
                open_time = shift["open"]
                close_time = shift["close"]
                hours_string = f"{hours_string} {open_time} - {close_time}"
        for day_pair in day_pairs:
            if day_pair[0] not in hours_string and day_pair[1] not in hours_string:
                hours_string = hours_string.replace("Today", day_pair[0]).replace("Tomorrow", day_pair[1])
                break
        oh = OpeningHours()
        oh.add_ranges_from_string(hours_string)
        return oh
