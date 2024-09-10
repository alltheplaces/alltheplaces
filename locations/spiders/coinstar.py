from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids


class CoinstarSpider(Spider):
    name = "coinstar"
    item_attributes = {"brand": "Coinstar", "brand_wikidata": "Q5141641"}
    max_results = 1000

    def start_requests(self):
        for lat, lon in country_iseadgg_centroids(["ca", "de", "es", "fr", "gb", "ie", "it", "us"], 158):
            yield JsonRequest(
                "https://coinstar.com/api?type=kiosk_selector",
                data={"radius": 100, "total_kiosks": self.max_results, "latitude": lat, "longitude": lon},
            )

    def parse(self, response):
        j = response.json()
        if j["status"] != "000":
            self.logger.error(j.get("status_text"))
            return

        kiosks = j["data"]
        if len(kiosks) >= self.max_results:
            raise RuntimeError("Results truncated, need to use a larger max_results.")

        for kiosk in kiosks:
            item = DictParser.parse(kiosk)
            item["ref"] = kiosk["machine_placement_id"]
            item["located_in"] = kiosk["banner_name"]
            item["street_address"] = kiosk["street_address_text"]
            item["state"] = kiosk["state_province_code"]
            item["website"] = f"https://coinstar.com/kiosk-info?KioskId={kiosk['machine_placement_id']}"
            yield item
