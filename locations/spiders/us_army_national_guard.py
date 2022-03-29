import scrapy
from locations.items import GeojsonPointItem

URL = "https://www.nationalguard.com/api/state/"

US_STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "USPR",
    "USGU",
    "USVI",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]


class USArmyNationalGuardSpider(scrapy.Spider):
    name = "us_army_national_guard"
    item_attributes = {"brand": "US Army National Guard"}
    allowed_domains = ["www.nationalguard.com"]

    def start_requests(self):
        for state in US_STATES:
            url = "".join([URL, state])
            yield scrapy.Request(url, callback=self.parse_info)

    def parse_info(self, response):
        data = response.json()
        for row in data["locations"]:
            properties = {
                "name": row["name"],
                "ref": row["id"],
                "addr_full": row["address"],
                "state": row["state"],
                "phone": row["phone"],
                "lat": row["latitude"],
                "lon": row["longitude"],
            }

            yield GeojsonPointItem(**properties)
