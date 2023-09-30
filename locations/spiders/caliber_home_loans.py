import scrapy
from geonamescache import GeonamesCache

from locations.items import Feature


class CaliberHomeLoansSpider(scrapy.Spider):
    name = "caliber_home_loans"
    item_attributes = {
        "brand": "Caliber Home Loans",
        "brand_wikidata": "Q25055134",
        "country": "US",
    }
    allowed_domains = ["www.caliberhomeloans.com"]
    download_delay = 0.3

    def start_requests(self):
        for state in GeonamesCache().get_us_states():
            yield scrapy.http.Request(
                url=f"https://www.caliberhomeloans.com/Home/BranchList?stateCode={state}&LCSpeciality=all&SpanishSpeaking=no"
            )

    def parse(self, response, **kwargs):
        if data := response.json():
            for store in data:
                properties = {
                    "ref": store["BranchID"],
                    "name": store["Name"],
                    "street_address": store["Address"],
                    "city": store["City"],
                    "state": store["State"],
                    "postcode": store["ZipCode"],
                    "lat": store["Latitude"],
                    "lon": store["Longitude"],
                    "website": response.url,
                }

                yield Feature(**properties)
