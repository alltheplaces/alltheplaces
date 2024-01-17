import json

import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]


class IowaUniversitySpider(scrapy.Spider):
    name = "iowa_university"
    item_attributes = {
        "brand": "University of Iowa Hospitals and Clinics",
        "brand_wikidata": "Q7895561",
    }
    allowed_domains = ["algolia.net", "algolianet.com"]
    body = '{"requests":[{"indexName":"uihc_locations","params":"query=&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&page=%PAGE%&maxValuesPerFacet=100&facets=%5B%22services%22%2C%22field_patient_population%22%5D&tagFilters="}]}'
    headers = {
        "Content-Type": "application/json",
        "User-Agent": BROWSER_DEFAULT,
        "Origin": "https://uihc.org",
        "Referer": "https://uihc.org/locations",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Host": "6x6rkba85v-2.algolianet.com",
    }

    def _prepare_request(self, page_number):
        return scrapy.http.Request(
            url="https://6x6rkba85v-2.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia for vanilla JavaScript (lite) 3.30.0;instantsearch.js (4.0.0-beta.2);JS Helper (0.0.0-5a0352a)&x-algolia-application-id=6X6RKBA85V&x-algolia-api-key=82d9c12b5c362e709520d802b71137ce",
            method="POST",
            headers=self.headers,
            body=self.body.replace("%PAGE%", str(page_number)),
        )

    def start_requests(self):
        yield self._prepare_request(1)

    def parse(self, response):
        stores = json.loads(response.body)["results"][0]

        for store in stores["hits"]:
            properties = {
                "ref": store["objectID"],
                "name": store["title"],
                "street_address": store["field_address:thoroughfare"],
                "city": store["field_address:locality"],
                "state": store["field_address:administrative_area"],
                "postcode": store["field_address:postal_code"],
                "country": "US",
                "lat": store["field_geolocation:lat"],
                "lon": store["field_geolocation:lon"],
                "phone": store.get("field_location_phone"),
                "website": store["url"],
            }

            yield Feature(**properties)

        if stores["page"] < stores["nbPages"]:
            yield self._prepare_request(int(stores["page"]) + 1)
