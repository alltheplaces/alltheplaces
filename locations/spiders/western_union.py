import json

from scrapy import Spider
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.geo import country_coordinates
from locations.hours import OpeningHours


class WesternUnionSpider(Spider):
    name = "western_union"
    item_attributes = {"brand": "Western Union", "brand_wikidata": "Q861042", "extras": Categories.MONEY_TRANSFER.value}
    allowed_domains = ["www.westernunion.com"]
    # start_urls[0] is a GraphQL endpoint.
    start_urls = ["https://www.westernunion.com/router/"]
    download_delay = 0.2

    def request_page(self, country, latitude, longitude, page_number):
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
        # A radius of 350km is reported in the response to each
        # query, but this doesn't appear to be used because pages of
        # results covering an entire country are returned from a
        # single set of coordinates.
        data = {
            "query": "query locations($req:LocationInput) { locations(input: $req) }",
            "variables": {
                "req": {
                    "longitude": longitude,
                    "latitude": latitude,
                    "country": country,
                    "openNow": "",
                    "services": [],
                    "sortOrder": "Distance",
                    "pageNumber": str(page_number),
                }
            },
        }
        yield JsonRequest(url=self.start_urls[0], method="POST", headers=headers, data=data)

    def start_requests(self):
        # The GraphQL query conducts a reverse geocode of the
        # supplied coordinates, and matches it to the supplied
        # ISO 3166-2 alpha-2 country code. A mismatch will cause no
        # results to be returned.
        for country in country_coordinates():
            yield from self.request_page(country["isocode"], country["lat"], country["lon"], 1)

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
            yield item

        # On the first response per country, generate requests for
        # all subsequent pages of results for that country.
        request_data = json.loads(response.request.body)
        current_page = int(request_data["variables"]["req"]["pageNumber"])
        total_pages = response.json()["data"]["locations"]["pageCount"]
        if current_page == 1 and total_pages > 1:
            for page_number in range(2, total_pages, 1):
                yield from self.request_page(
                    request_data["variables"]["req"]["country"],
                    request_data["variables"]["req"]["latitude"],
                    request_data["variables"]["req"]["longitude"],
                    page_number,
                )
