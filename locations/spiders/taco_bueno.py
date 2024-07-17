import scrapy
from geonamescache import GeonamesCache

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TacobuenoSpider(scrapy.Spider):
    name = "bueno"
    item_attributes = {"brand": "Taco Bueno", "brand_wikidata": "Q7673958"}

    def start_requests(self):
        for state in GeonamesCache().get_us_states():
            yield scrapy.Request(f"https://buenoonthego.com/mp/ndXTAL/searchByStateCode_JSON?stateCode='{state}'")

    @staticmethod
    def convert_hours(times: dict) -> OpeningHours:
        if times == "Closed":
            return
        oh = OpeningHours()
        start_time, end_time = times.split(" - ")
        oh.add_days_range(DAYS, start_time, end_time, time_format="%I:%M %p")
        return oh

    def parse(self, response):
        results = response.json()
        if results:
            for i in results:
                ref = i["storeid"]
                name = i["restaurantname"]
                street = clean_address([i["address1"], i["address2"], i["address3"]])
                city = i["city"]
                state = i["statecode"]
                postcode = i["zipcode"]
                country = i["country"]
                phone = i["phone"]
                lon = i["longitude"]
                lat = i["latitude"]
                # business_hours seems to hold bad data
                hours = self.convert_hours(i["businesshours"])
                yield Feature(
                    ref=ref,
                    name=name,
                    street_address=street,
                    city=city,
                    state=state,
                    postcode=postcode,
                    country=country,
                    phone=phone,
                    lon=lon,
                    lat=lat,
                    opening_hours=hours,
                )
