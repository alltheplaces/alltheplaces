import re
from urllib.parse import urlparse

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address
from locations.user_agents import BROWSER_DEFAULT

BRANDS = {
    "https://www.bakersplus.com/": {"brand": "Baker's", "brand_wikidata": "Q4849080"},
    "https://www.citymarket.com/": {"brand": "City Market", "brand_wikidata": "Q5123299"},
    "https://www.dillons.com/": {"brand": "Dillons", "brand_wikidata": "Q5276954"},
    "https://www.food4less.com/": {"brand": "Food 4 Less", "brand_wikidata": "Q5465282"},
    "https://www.foodsco.net/": {"brand": "Foods Co", "brand_wikidata": "Q5465282"},
    "https://www.fredmeyer.com/": {"brand": "Fred Meyer", "brand_wikidata": "Q5495932"},
    "https://www.frysfood.com/": {"brand": "Fry's Food Stores", "brand_wikidata": "Q5506547"},
    "https://www.gerbes.com/": {"brand": "Gerbes", "brand_wikidata": "Q5276954"},
    "https://www.harristeeter.com/": {"brand": "Harris Teeter", "brand_wikidata": "Q5665067"},
    "https://www.jaycfoods.com/": {"brand": "JayC", "brand_wikidata": "Q6166302"},
    "https://www.kingsoopers.com/": {"brand": "King Soopers", "brand_wikidata": "Q6412065"},
    "https://www.kroger.com/": {"brand": "Kroger", "brand_wikidata": "Q153417"},
    "https://www.marianos.com/": {"brand": "Mariano's Fresh Market", "brand_wikidata": "Q55622168"},
    "https://www.metromarket.net/": {"brand": "Metro Market", "brand_wikidata": "Q7371288"},
    "https://www.pay-less.com/": {"brand": "Pay Less", "brand_wikidata": "Q7156587"},
    "https://www.picknsave.com/": {"brand": "Pick 'n Save", "brand_wikidata": "Q7371288"},
    "https://www.qfc.com/": {"brand": "QFC", "brand_wikidata": "Q7265425"},
    "https://www.ralphs.com/": {"brand": "Ralphs", "brand_wikidata": "Q3929820"},
    "https://www.smithsfoodanddrug.com/": {"brand": "Smith's", "brand_wikidata": "Q7544856"},
}


class KrogerUSSpider(SitemapSpider):
    name = "kroger_us"
    sitemap_urls = [f"{brand}storelocator-sitemap.xml" for brand in BRANDS.keys()]
    custom_settings = {"AUTOTHROTTLE_ENABLED": True, "USER_AGENT": BROWSER_DEFAULT}
    url_re = re.compile(r"/(\d{3})/(\d{5})$")

    def sitemap_filter(self, entries):
        location_ids = []
        brand_domain = ""
        for entry in entries:
            if m := re.search(self.url_re, entry["loc"]):
                location_ids.append("{}{}".format(*m.groups()))
                if not brand_domain:
                    brand_domain = urlparse(entry["loc"]).hostname
        location_groups = [location_ids[i : i + 25] for i in range(0, len(location_ids), 25)]
        for location_group in location_groups:
            new_entry = {
                "loc": f"https://{brand_domain}/atlas/v1/stores/v2/locator?filter.locationIds="
                + ",".join(location_group),
                "lastmod": "2000-01-01T00:00:00+00:00",
                "changefreq": "daily",
                "priority": "1.0",
            }
            yield new_entry

    def parse(self, response, **kwargs):
        for location in response.json()["data"]["stores"]:
            properties = {
                "ref": location["locationId"],
                "name": location["vanityName"],
                "lat": location["locale"]["location"]["lat"],
                "lon": location["locale"]["location"]["lng"],
                "street_address": clean_address(location["locale"]["address"]["addressLines"]),
                "city": location["locale"]["address"]["cityTown"],
                "postcode": location["locale"]["address"]["postalCode"],
                "state": location["locale"]["address"]["stateProvince"],
                "country": location["locale"]["address"]["countryCode"],
                "phone": location["phoneNumber"].get("raw"),
                "extras": {"operator": location["legalName"]},
            }

            for url, brand in BRANDS.items():
                if response.url.startswith(url):
                    properties.update(brand)
                    break

            properties["opening_hours"] = self.parse_hours(location.get("prettyHours", []))

            if location["banner"] == "thelittleclinic":
                properties["brand"] = "The Little Clinic"
                properties["brand_wikidata"] = "Q64138262"
                apply_category(Categories.PHARMACY, properties)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, properties)
                yield from self.parse_colocated_pharmacy(properties, location)

            yield Feature(**properties)

    def parse_colocated_pharmacy(self, supermarket_properties, location):
        for department in location.get("departments"):
            if department["code"] != "09":
                continue
            properties = {
                "ref": supermarket_properties["ref"]
                + "P",  # No unique identifier for colocated pharmacies, so add "P" to differentiate from supermarkets.
                "name": supermarket_properties["name"],
                "brand": supermarket_properties["brand"],
                "brand_wikidata": supermarket_properties["brand_wikidata"],
                "phone": department["phoneNumber"].get("raw"),
                "extras": {"operator": supermarket_properties["extras"]["operator"]},
            }
            if department.get("locale"):
                properties["lat"] = department["locale"]["location"]["lat"]
                properties["lon"] = department["locale"]["location"]["lng"]
                properties["street_address"] = clean_address(department["locale"]["address"]["addressLines"])
                properties["city"] = department["locale"]["address"]["cityTown"]
                properties["postcode"] = department["locale"]["address"]["postalCode"]
                properties["state"] = department["locale"]["address"]["stateProvince"]
                properties["country"] = department["locale"]["address"]["countryCode"]
            else:
                properties["lat"] = supermarket_properties.get("lat")
                properties["lon"] = supermarket_properties.get("lon")
                properties["street_address"] = supermarket_properties.get("street_address")
                properties["city"] = supermarket_properties.get("city")
                properties["postcode"] = supermarket_properties.get("postcode")
                properties["state"] = supermarket_properties.get("state")
                properties["country"] = supermarket_properties.get("country")

            properties["opening_hours"] = self.parse_hours(department.get("prettyHours", []))

            apply_category(Categories.PHARMACY, properties)

            yield Feature(**properties)

    @staticmethod
    def parse_hours(rules: [dict]) -> OpeningHours:
        hours_string = ""
        for day_hours in rules:
            hours_string = "{} {}: {}".format(hours_string, day_hours["displayName"], day_hours["displayHours"])

        oh = OpeningHours()
        oh.add_ranges_from_string(hours_string)
        return oh
