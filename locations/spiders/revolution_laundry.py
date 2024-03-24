import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class RevolutionLaundry(Spider):
    name = "revolution_laundry"
    item_attributes = {"brand_wikidata": "Q113516904"}
    companies = [
        {"id": "50", "latitude": 52.907816395096205, "longitude": -4.217292850000035},  # UK
        {"id": "44", "latitude": 51.08611645, "longitude": 6.98378445},  # Germany
        {"id": "3", "latitude": 48.8534951, "longitude": 2.3483915},  # France
        {"id": "56", "latitude": 50.901236749999995, "longitude": 4.4845285},  # Belgium
        {"id": "62", "latitude": 52.378, "longitude": 4.9},  # Netherlands
        {"id": "47", "latitude": 42.29443574654067, "longitude": 17.26184720770675},  # Austria
        {"id": "65", "latitude": 41.382894, "longitude": 2.177432},  # Barcelona - only 50? Better midpoint wanted.
        {"id": "59", "latitude": 46.409894989781066, "longitude": 8.765714479904148},  # Switzerland # Only 9!
        {"id": "68", "latitude": 38.74712, "longitude": -9.164427},  # Portugal
    ]

    def start_requests(self):
        for company in self.companies:
            yield JsonRequest(
                url="https://stores.revolution-laundry.com/Ajax/searchByCoordinates",
                data={
                    "company": {"companyId": company["id"]},
                    "location": {
                        "geoCoordinates": {
                            "latitude": company["latitude"],
                            "longitude": company["longitude"],
                            "geoCircle": 10000000,
                        }
                    },
                    "machineFamily": {"familyId": 6},
                    "pagination": {"pageNumber": 1, "pageSize": 99999},
                },
                method="POST",
                callback=self.parse,
            )

    def parse(self, response):
        for result in json.loads(response.json()["data"])["data"]:
            item = DictParser.parse(result["location"])
            item["lat"] = result["location"]["geoCoordinates"]["latitude"]
            item["lon"] = result["location"]["geoCoordinates"]["longitude"]

            yield item
