import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class DhlExpressEsSpider(scrapy.Spider):
    name = "dhl_express_es"
    item_attributes = {"brand": "DHL", "brand_wikidata": "Q489815"}
    allowed_domains = ["wsbexpress.dhl.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        point_files = "eu_centroids_80km_radius_country.csv"
        for lat, lon in point_locations(point_files, "ES"):
            url = f"https://wsbexpress.dhl.com/ServicePointLocator/restV3/servicepoints?servicePointResults=1000000&address=U3BhaW4&latitude={lat}&longitude={lon}&countryCode=ES&weightUom=lb&dimensionsUom=in&languageScriptCode=Latn&language=eng&resultUom=mi&b64=true&key=963d867f-48b8-4f36-823d-88f311d9f6ef"
            yield scrapy.Request(url=url)

    def parse(self, response):
        if not response.json().get("servicePoints"):
            return
        for data in response.json().get("servicePoints"):
            if data.get("servicePointType") in ["STATION", "CITY"] and data.get("address", {}).get("country") == "ES":
                item = DictParser.parse(data.get("address"))
                item["ref"] = data.get("facilityId")
                item["name"] = data.get("localName")
                item["lat"] = data.get("geoLocation", {}).get("latitude")
                item["lon"] = data.get("geoLocation", {}).get("longitude")
                item["phone"] = data.get("contactDetails", {}).get("phoneNumber")
                item["website"] = data.get("contactDetails", {}).get("linkUri")
                oh = OpeningHours()
                for day in data.get("openingHours", {}).get("openingHours"):
                    oh.add_range(
                        day=day.get("dayOfWeek"), open_time=day.get("openingTime"), close_time=day.get("closingTime")
                    )
                item["opening_hours"] = oh.as_opening_hours()
                apply_category(Categories.POST_OFFICE, item)

                yield item
