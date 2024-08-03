from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class TasmanianGovernmentFreeWifiAUSpider(Spider):
    name = "tasmanian_government_free_wifi_au"
    item_attributes = {"operator": "Government of Tasmania", "operator_wikidata": "Q3112571"}
    allowed_domains = ["freewifi.tas.gov.au"]
    start_urls = ["https://freewifi.tas.gov.au/api/application.json"]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["locations"]:
            for hotspot in location.get("hotspots", []):
                if hotspot["disabled"]:
                    continue
                properties = {
                    "name": hotspot["label"],
                    "lat": hotspot["latitude"],
                    "lon": hotspot["longitude"],
                    "city": location["title"]["en"],
                    "state": "Tasmania",
                    "extras": {
                        "internet_access": "wlan",
                        "internet_access:fee": "no",
                        "internet_access:operator": "Telstra",
                        "internet_access:operator:wikidata": "Q721162",
                        "internet_access:ssid": "TasGov_Free",
                    },
                }
                apply_category(Categories.ANTENNA, properties)
                yield Feature(**properties)
