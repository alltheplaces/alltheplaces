from scrapy import Request, Spider

from locations.dict_parser import DictParser

# API documentation:
# https://www.algolia.com/doc/rest-api/search/
#
# To use this spider, specify the API key and application ID as sent in the
# headers of a query request, as well as the name of the "index" found in either
# the request URL or in query parameters in the request body. Override
# parse_item to extract attributes from each object.


class AlgoliaSpider(Spider):
    dataset_attributes = {"source": "api", "api": "algolia"}

    api_key = ""
    app_id = ""
    index_name = ""

    def _make_request(self, cursor):
        url = f"https://{self.app_id}-dsn.algolia.net/1/indexes/{self.index_name}/browse"
        if cursor is not None:
            url += f"?cursor={cursor}"
        return Request(url=url, headers={"x-algolia-api-key": self.api_key, "x-algolia-application-id": self.app_id})

    def start_requests(self):
        yield self._make_request(None)

    def parse(self, response):
        js = response.json()
        for location in js["hits"]:
            item = DictParser.parse(location)
            yield from self.parse_item(item, location) or []

        if "cursor" in js:
            yield self._make_request(js["cursor"])

    def parse_item(self, item, location):
        yield item
