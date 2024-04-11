import json

from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class WesternUnionSpider(Spider):
    name = "western_union"
    item_attributes = {
        "brand": "Western Union",
        "brand_wikidata": "Q861042",
        "extras": {"money_transfer": "western_union"},
    }
    allowed_domains = ["www.westernunion.com"]
    # start_urls[0] is a GraphQL endpoint.
    start_urls = ["https://www.westernunion.com/router/"]
    download_delay = 0.2

    def request_page(self, latitude, longitude, page_number):
        # An access code for querying the GraphQL endpoint is
        # required, This is constant across different browser
        # sessions and the same for all users of the website.
        headers = {
            "x-wu-accesscode": "RtYV3XDz9EA",
            "x-wu-operationName": "locations",
        }
        # The GraphQL query does not appear to allow for the page
        # size to be increased. Typically the page size is observed
        # by default to be 15 results per page.
        #
        # A radius of 350km is used by the API to search around each
        # provided coordinate. There does not appear to be a way to
        # specify an alternative radius.
        data = {
            "query": "query locations($req:LocationInput) { locations(input: $req) }",
            "variables": {
                "req": {
                    "longitude": str(longitude),
                    "latitude": str(latitude),
                    "country": "US",  # Seemingly has no effect.
                    "brand": "wu",
                    "openNow": "",
                    "services": [],
                    "sortOrder": "Distance",
                    "pageNumber": str(page_number),
                }
            },
        }
        yield JsonRequest(url=self.start_urls[0], method="POST", headers=headers, data=data)

    def start_requests(self):
        # The GraphQL query searches for locations within a 350km
        # radius of supplied coordinates, then returns locations in
        # pages of 15 locations each page.
        for lat, lon in point_locations("earth_centroids_iseadgg_346km_radius.csv"):
            yield from self.request_page(lat, lon, 1)

    def parse(self, response):
        # If crawling too fast, the server responds with a JSON
        # blob containing an error message. Schedule a retry.
        if "results" not in response.json()["data"]["locations"]:
            if "errorCode" in response.json()["data"]["locations"]:
                if response.json()["data"]["locations"]["errorCode"] == 500:
                    yield get_retry_request(
                        response.request, spider=self, max_retry_times=5, reason="Retry after rate limiting error"
                    )
                    return
            # In case of an unhandled error, skip parsing.
            return

        # Parse the 15 (or fewer) locations from the response provided.
        for location in response.json()["data"]["locations"]["results"]:
            item = DictParser.parse(location)
            item["website"] = "https://location.westernunion.com/" + location["detailsUrl"]
            item["opening_hours"] = OpeningHours()
            hours_string = " ".join([f"{day}: {hours}" for (day, hours) in location["detail.hours"].items()])
            item["opening_hours"].add_ranges_from_string(hours_string)

            apply_yes_no(Extras.ATM, item, location["atmLocation"] == "Y")
            apply_category(Categories.BANK, item)
            yield item

        # On the first response per radius search of a coordinate,
        # generate requests for all subsequent pages of results
        # found by the API within the 350km search radius.
        request_data = json.loads(response.request.body)
        current_page = int(request_data["variables"]["req"]["pageNumber"])
        total_pages = response.json()["data"]["locations"]["pageCount"]
        if current_page == 1 and total_pages > 1:
            for page_number in range(2, total_pages, 1):
                yield from self.request_page(
                    request_data["variables"]["req"]["latitude"],
                    request_data["variables"]["req"]["longitude"],
                    page_number,
                )
