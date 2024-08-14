from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class TjxSpider(Spider):
    name = "tjx"
    allowed_domains = ["marketingsl.tjx.com"]

    # Source of chain IDs is the
    # JavaScript switch statement
    # "switch (location['Chain']) {"
    # within https://www.tjx.com/stores
    chains = {
        # USA chains
        "08": ({"brand": "TJ Maxx", "brand_wikidata": "Q10860683"}, ["US"]),
        "10": ({"brand": "Marshalls", "brand_wikidata": "Q15903261"}, ["US"]),
        "28": ({"brand": "HomeGoods", "brand_wikidata": "Q5887941"}, ["US"]),
        "29": ({"brand": "HomeSense", "brand_wikidata": "Q16844433"}, ["US"]),
        "50": ({"brand": "Sierra", "brand_wikidata": "Q7511598"}, ["US"]),
        # Canada chains
        "90": ({"brand": "HomeSense", "brand_wikidata": "Q16844433"}, ["CA"]),
        "91": ({"brand": "Winners", "brand_wikidata": "Q845257"}, ["CA"]),
        "93": ({"brand": "Marshalls", "brand_wikidata": "Q15903261"}, ["CA"]),
        # Europe and Australia chains
        "20": ({"brand": "TK Maxx", "brand_wikidata": "Q23823668"}, ["GB", "IE", "DE", "PL", "AT", "NL", "AU"]),
        "21": ({"brand": "HomeSense", "brand_wikidata": "Q16844433"}, ["GB", "IE"]),
    }

    country_centroids = {
        "AU": "au_centroids_iseadgg_48km_radius.csv",
        "AT": "at_centroids_iseadgg_48km_radius.csv",
        "CA": "ca_centroids_iseadgg_48km_radius.csv",
        "DE": "de_centroids_iseadgg_48km_radius.csv",
        "IE": "ie_centroids_iseadgg_48km_radius.csv",
        "NL": "nl_centroids_iseadgg_48km_radius.csv",
        "PL": "pl_centroids_iseadgg_48km_radius.csv",
        "UK": "gb_centroids_iseadgg_48km_radius.csv",
        "US": "us_centroids_iseadgg_48km_radius.csv",
    }

    def start_requests(self):
        for country_code, centroids_file in self.country_centroids.items():
            chains = [k for k in self.chains.keys() if country_code in self.chains[k][1]]
            for lat, lon in point_locations(centroids_file):
                yield FormRequest(
                    url="https://marketingsl.tjx.com/storelocator/GetSearchResults",
                    formdata={
                        "chain": ",".join(chains),
                        "lang": "en",
                        "geolat": str(lat),
                        "geolong": str(lon),
                    },
                    headers={"Accept": "application/json"},
                )

    def parse(self, response):
        for location in response.json()["Stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["Chain"] + location["StoreID"]

            if location["Chain"] in self.chains.keys():
                item["brand"] = self.chains[location["Chain"]][0]["brand"]
                item["brand_wikidata"] = self.chains[location["Chain"]][0]["brand_wikidata"]

            item["street_address"] = clean_address([location.get("Address"), location.get("Address2")])
            item.pop("addr_full", None)
            if location["Country"] not in ["CA", "US"]:
                item.pop("state", None)  # Outside of CA and US, the "State"
                # field is incorrectly the country
                # name.

            if location.get("Hours"):  # Hours can sometimes be None.
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location.get("Hours"))

            yield item
