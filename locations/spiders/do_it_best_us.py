import re
from typing import AsyncIterator, Iterable

import pycountry
from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.items import Feature

GRAPHQL_QUERY = """
query GetStoreLocatorQuery($lat: String, $long: String, $distance: Int, $limit: Int) {
    storeLocator(filter: { lat: $lat, lng: $long, distance: $distance, limit: $limit }) {
        store {
            name
            street
            city
            state
            zipcode
            lat
            lng
            phone_number
            tvstoreid
            member_number
        }
    }
}
"""


class DoItBestUSSpider(Spider):
    name = "do_it_best_us"
    item_attributes = {"brand": "Do it Best", "brand_wikidata": "Q5286067"}
    allowed_domains = ["doitbest.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    us_states = {subdivision.code[-2:] for subdivision in pycountry.subdivisions.get(country_code="US")}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.doitbest.com/find-a-store/", callback=self.parse_locator_token)

    def parse_locator_token(self, response: Response) -> Iterable[JsonRequest]:
        # The GraphQL API rejects requests without this header. Its value is
        # published in the page's own "store-config" meta tag, so it is
        # fetched fresh rather than hardcoded in case it rotates on a future
        # site deployment.
        token = re.search(r"dibcommercerestriction&#34;:&#34;([a-zA-Z0-9]+)&#34;", response.text).group(1)
        headers = {"dibcommercerestriction": token}
        for lat, lon in country_iseadgg_centroids("US", 458):
            yield JsonRequest(
                url="https://www.doitbest.com/api/graphql",
                data={
                    "query": GRAPHQL_QUERY,
                    "variables": {"lat": str(lat), "long": str(lon), "distance": 285, "limit": 2000},
                },
                headers=headers,
                callback=self.parse,
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        stores = response.json()["data"]["storeLocator"]["store"] or []

        if len(stores) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(stores))

        if len(stores) >= 2000:
            raise RuntimeError(
                "Locations have probably been truncated since 2000 (or more) locations were returned by a single geographic radius search. Use a smaller search radius."
            )

        for store in stores:
            if store.get("tvstoreid"):
                # Do It Best acquired True Value in 2024 and the rebrand is
                # still incomplete: stores still sold and branded as True
                # Value are also returned by this API, tagged with a
                # tvstoreid. Those are covered by the separate
                # true_value_us spider instead, so skip them here to avoid
                # duplicating locations across both spiders.
                continue
            if store.get("state") not in self.us_states:
                # Do It Best also has member stores outside the US (e.g.
                # Mexico, Central America, the Caribbean); this spider is
                # scoped to the US only.
                continue

            item = DictParser.parse(store)
            item["ref"] = store.get("member_number")
            apply_category(Categories.SHOP_HARDWARE, item)
            yield item
