import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class BaptistHealthArkansasUSSpider(scrapy.Spider):
    name = "bha_us"
    item_attributes = {
        "brand": "Baptist Health Foundation",
        "brand_wikidata": "Q50379824",
    }
    allowed_domains = ["algolia.net", "baptist-health.com"]

    def start_requests(self):
        yield JsonRequest(
            url="https://6eh1ib012d-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.33.0)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(3.6.0)%3B%20Vue%20(2.6.10)%3B%20Vue%20InstantSearch%20(2.3.0)%3B%20JS%20Helper%20(2.28.0)&x-algolia-application-id=6EH1IB012D&x-algolia-api-key=66eafc59867885378e0a81317ea35987",
            data={
                "requests": [
                    {
                        "indexName": "wp_posts_location",
                        "params": "query=&hitsPerPage=500&maxValuesPerFacet=150&page=0&facets=%5B%22city%22%2C%22facility_type%22%5D&tagFilters=",
                    }
                ]
            },
            callback=self.parse_stores,
        )

    def parse_stores(self, response):
        for i in response.json()["results"]:
            first_value = list(i.values())[0]
            for j in first_value:
                item = Feature()
                item["name"] = j["post_title"]
                item["ref"] = j["permalink"]
                item["website"] = j["permalink"]
                item["image"] = j["image"]
                item["street_address"] = merge_address_lines([j["address_1"], j["address_2"]])
                item["city"] = j["city"]
                item["state"] = j["state"]
                item["postcode"] = j["zip_code"]
                item["country"] = "US"
                item["phone"] = j["phone_number"]
                item["lat"] = float(j["_geoloc"]["lat"])
                item["lon"] = float(j["_geoloc"]["lng"])
                if facility_type := j.get("facility_type"):
                    if "Hospitals" in facility_type:
                        apply_category(Categories.HOSPITAL, item)
                    elif "Urgent Care" in facility_type:
                        apply_category(Categories.CLINIC_URGENT, item)
                    else:
                        apply_category(Categories.CLINIC, item)
                yield item
