import re
from typing import Any, Iterable
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The store locator is a JavaScript application that reads locations from the
# Gorilla Dash GraphQL API. That API only accepts persisted queries (sending
# query text is rejected with a 403), and needs a bearer token, which the
# locator page publishes as window.graphqlToken. The token is short lived, so
# the spider reads a fresh one from the page on every run.
#
# No brand:wikidata is set because the chain has no Wikidata item.

GRAPHQL_URL = "https://graphql.gorilladash.com/graphql"
PERSISTED_QUERY_HASH = "1767aab544685ec9a6b69ef2346aaaaf66a965c65b1d22a17050553a6202b5c6"


class GrazeCrazeUSSpider(Spider):
    name = "graze_craze_us"
    item_attributes = {"brand": "Graze Craze"}
    allowed_domains = ["www.grazecraze.com", "graphql.gorilladash.com"]
    start_urls = ["https://www.grazecraze.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        if not (token := re.search(r'window\.graphqlToken\s*=\s*"([^"]+)"', response.text)):
            self.logger.error("No GraphQL token on the locator page")
            return

        parameters = {
            "operationName": "getTribes",
            "variables": '{"tribeType":"Graze Craze Stores","order":["name"],"status":"all"}',
            "extensions": '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}' % PERSISTED_QUERY_HASH,
        }
        yield JsonRequest(
            url=f"{GRAPHQL_URL}?{urlencode(parameters)}",
            headers={"Authorization": f"Bearer {token.group(1)}", "Referer": "https://www.grazecraze.com/"},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["data"]["tribes"]:
            # Franchises that have not opened yet are "Opening Soon", and the
            # brand keeps one "Testing" record in the feed.
            if location.get("status") != "Active":
                continue

            item = DictParser.parse(location)
            item["ref"] = location["slug"]
            item["branch"] = location["name"]
            item["name"] = None
            item["street_address"] = merge_address_lines([location.get("address_1"), location.get("address_2")])
            item["city"] = location.get("locality")
            item["state"] = location.get("state_abbreviated")
            item["phone"] = location.get("main_telephone")
            item["email"] = location.get("public_email")
            item["website"] = f"https://www.grazecraze.com/locations/{location['slug']}"
            item["facebook"] = location.get("social_facebook_url")
            item["extras"]["contact:instagram"] = location.get("social_instagram_url")

            apply_category(Categories.SHOP_DELI, item)
            item["extras"]["cuisine"] = "charcuterie"

            yield item
