import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class TjxSpider(scrapy.Spider):
    name = "tjx"
    allowed_domains = ["tjx.com"]

    chains = {
        # USA chains
        "08": {"brand": "TJ Maxx", "brand_wikidata": "Q10860683", "country": "USA"},
        "10": {"brand": "Marshalls", "brand_wikidata": "Q15903261", "country": "USA"},
        # Canada chains
        "90": {"brand": "HomeSense", "brand_wikidata": "Q16844433", "country": "Canada"},
        "91": {"brand": "Winners", "brand_wikidata": "Q845257", "country": "Canada"},
        "93": {"brand": "Marshalls", "brand_wikidata": "Q15903261", "country": "Canada"},
        # There are separate spiders for below brands that provide better data
        "28": {"brand": "HomeGoods", "brand_wikidata": "Q5887941", "country": "USA"},
        "50": {"brand": "Sierra", "brand_wikidata": "Q7511598", "country": "USA"},
    }

    countries = {"Canada": "ca_centroids_100mile_radius.csv", "USA": "us_centroids_50mile_radius.csv"}

    def start_requests(self):
        for country, centroids_file in self.countries.items():
            chains = [k for k in self.chains.keys() if self.chains[k]["country"] == country]
            self.logger.info(f"Found {len(chains)} chains for {country}")
            for lat, lon in point_locations(centroids_file):
                yield scrapy.http.FormRequest(
                    url="https://marketingsl.tjx.com/storelocator/GetSearchResults",
                    formdata={
                        "chain": ",".join(chains),
                        "lang": "en",
                        "geolat": str(lat),
                        "geolong": str(lon),
                    },
                    headers={"Accept": "application/json"},
                )

    def parse_hours(self, item, store):
        """Mon-Thu: 9am - 9pm, Black Friday: 8am - 10pm, Sat: 9am - 9pm, Sun: 10am - 8pm"""
        if hours := store.get("Hours"):
            try:
                hours = hours.replace("Black Friday", "Fri")
                opening_hours = OpeningHours()
                opening_hours.add_ranges_from_string(hours)
                item["opening_hours"] = opening_hours.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Couldn't parse hours for {item['ref']}: {hours}, {e}")

    def parse(self, response):
        data = response.json()
        for store in data["Stores"]:
            if not self.chains.get(store["Chain"]):
                self.logger.error(f"Unknown chain: {store['Chain']}")
                continue
            item = DictParser.parse(store)
            item["ref"] = f'{store["Chain"]}{store["StoreID"]}'
            item["brand"] = self.chains.get(store["Chain"], {}).get("brand")
            item["brand_wikidata"] = self.chains.get(store["Chain"], {}).get("brand_wikidata")
            self.parse_hours(item, store)
            yield item
