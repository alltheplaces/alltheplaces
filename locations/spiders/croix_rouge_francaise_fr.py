from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours, sanitise_day


class CroixRougeFrancaiseFRSpider(Spider):
    name = "croix_rouge_francaise_fr"
    item_attributes = {"brand": "Croix-Rouge Française", "brand_wikidata": "Q3003244"}
    allowed_domains = ["backend.structure.croix-rouge.fr"]
    start_urls = ["https://backend.structure.croix-rouge.fr/graphql"]

    def start_requests(self):
        graphql_query = """query GET_SEARCH_STRUCTURE_ELASTICSEARCH_QUERY($actionIds: [ID], $activityIds: [ID], $from: Int, $lat: Float, $lon: Float, $search: String!, $size: Int) {
    searchStructuresDocuments(
        actionIds: $actionIds
        activityIds: $activityIds
        from: $from
        lat: $lat
        lon: $lon
        search: $search
        size: $size
    ) {
        items {
            actions
            activities { activity }
            address_complement
            address_number
            address_place
            address_street
            address_street_type
            city
            contentful_content_id
            distance
            id
            latitude
            longitude
            name
            slug
            schedule
            specialities
            structure_type
            zip_code
        }
    }
}"""
        data = {
            "operationName": "GET_SEARCH_STRUCTURE_ELASTICSEARCH_QUERY",
            "query": graphql_query,
            "variables": {
                "actionIds": [],
                "activityIds": [],
                "from": 0,
                "lat": 44.8624,
                "lon": -0.5848,
                "search": "",
                "size": 10000,
            },
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data)

    def parse(self, response):
        for location in response.json()["data"]["searchStructuresDocuments"]["items"]:
            item = DictParser.parse(location)
            if location.get("address_complement"):
                item["street_address"] = location["address_complement"]
            if location.get("slug"):
                item["website"] = "https://www.croix-rouge.fr/" + location["slug"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["schedule"]:
                item["opening_hours"].add_range(
                    sanitise_day(day_hours["day"], DAYS_FR), day_hours["open"], day_hours["closed"]
                )
            yield item
