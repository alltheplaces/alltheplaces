import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


# On the date of writing (2023-12-20) the website blocks the spider with a captcha
# after ~150 requests with current settings, so we are not getting all POIs.
class WalmartCASpider(scrapy.Spider):
    name = "walmart_ca"
    allowed_domains = ["www.walmart.ca"]
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551"}
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 15,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        url_template = "https://www.walmart.ca/en/stores-near-me/api/searchStores?singleLineAddr={city}"
        for city in city_locations("CA"):
            yield scrapy.Request(url_template.format(city=city["name"]))

    def parse(self, response):
        if "blocked" in response.url:
            self.logger.error(f"Blocked by Walmart {response.url}")
            raise scrapy.exceptions.CloseSpider("blocked")

        self.logger.info(f"Parsing {response.url}")
        self.logger.info(f"GOT POIs: {len(response.json()['payload']['stores'])}")
        for poi in response.json()["payload"]["stores"]:
            if poi.get("deleted"):
                self.crawler.stats.inc_value("atp/poi/closed")
                continue

            poi.update(poi.pop("address"))
            poi.update(poi.pop("geoPoint"))
            item = DictParser.parse(poi)

            item["opening_hours"] = self.parse_hours(poi.get("regularHours"))

            # TODO: parse more categories under 'servicesMap' key
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item

    def parse_hours(self, hours):
        if not hours:
            return None

        try:
            oh = OpeningHours()
            for hour in hours:
                oh.add_range(hour.get("day"), hour.get("start"), hour.get("end"))
            return oh.as_opening_hours()
        except Exception as e:
            self.logger.error(f"Failed to parse hours: {hours}, {e}")
            return None
