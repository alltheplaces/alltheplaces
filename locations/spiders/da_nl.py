from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DaNLSpider(Spider):
    name = "da_nl"
    start_urls = ["https://www.da.nl/api/graphql"]
    allowed_domains = ["www.da.nl"]
    item_attributes = {"brand": "DA", "brand_wikidata": "Q4899756", "extras": Categories.SHOP_CHEMIST.value}

    def start_requests(self):
        graphql_query = """query GetRetailStores($storeId: Int = 3) {
    retailStores(pageSize: 5000, storeId: $storeId) {
        id
        path
        pickup_location_code
        description
        short_description
        image_paths
        relation_nr
        name
        street
        postcode
        city
        opening_times {
            day_of_week
            status
            open
            close
            lunch_start
            lunch_stop
        }
        latitude
        longitude
        services {
            label
        }
        phone
        opening_times_extra_text
        curbside_enabled
    }
}"""
        data = {"operationName": "GetRetailStores", "variables": {"storeId": 3}, "query": graphql_query}
        yield JsonRequest(url=self.start_urls[0], method="POST", data=data)

    def parse(self, response):
        for location in response.json()["data"]["retailStores"]:
            location["id"] = location.pop("relation_nr")
            location["street_address"] = location.pop("street", "").replace("\\n", " ")
            location["website"] = "https://www.da.nl/winkel/{}".format(location["path"])
            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for day_hours in location["opening_times"]:
                if not day_hours["status"]:  # Closed on this day
                    continue
                if day_hours["lunch_start"] and day_hours["lunch_stop"]:
                    item["opening_hours"].add_range(
                        DAYS[day_hours["day_of_week"] - 1], day_hours["open"], day_hours["lunch_start"]
                    )
                    item["opening_hours"].add_range(
                        DAYS[day_hours["day_of_week"] - 1], day_hours["lunch_stop"], day_hours["close"]
                    )
                else:
                    item["opening_hours"].add_range(
                        DAYS[day_hours["day_of_week"] - 1], day_hours["open"], day_hours["close"]
                    )

            yield item
