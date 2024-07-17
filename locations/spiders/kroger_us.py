import re
from copy import deepcopy
from typing import Iterable
from urllib.parse import urljoin, urlparse

from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.spiders.sitemap import iterloc
from scrapy.utils.sitemap import Sitemap

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import FIREFOX_LATEST

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
    custom_settings = {"AUTOTHROTTLE_ENABLED": True}
    url_re = re.compile(r"/(\d{3})/(\d{5})$")
    requires_proxy = True
    user_agent = FIREFOX_LATEST

    departments = {
        "09": Categories.PHARMACY,
        "10": Categories.FUEL_STATION,
    }

    def _parse_sitemap(self, response):
        brand_domain = urlparse(response.url).hostname

        location_ids = []
        for url in iterloc(Sitemap(self._get_sitemap_body(response))):
            if m := re.search(self.url_re, url):
                location_ids.append(("{}{}".format(*m.groups()), url))

        for chunk in [location_ids[i : i + 25] for i in range(0, len(location_ids), 25)]:
            url_map = {}
            for ref, url in chunk:
                url_map[ref] = url

            yield Request(
                url="https://{}/atlas/v1/stores/v2/locator?filter.locationIds={}".format(
                    brand_domain,
                    ",".join(url_map.keys()),
                ),
                meta={"url_map": url_map},
                errback=self.parse_error,
            )

    def parse_error(self, failure, **kwargs):
        for ref in failure.request.meta["url_map"].keys():
            yield Request(
                url=urljoin(failure.request.url, f"/atlas/v1/stores/v2/locator?filter.locationIds={ref}"),
                meta={"url_map": failure.request.meta["url_map"]},
            )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]["stores"]:
            properties = {
                "ref": location["locationId"],
                "name": location["facilityName"],
                "lat": location["locale"]["location"]["lat"],
                "lon": location["locale"]["location"]["lng"],
                "street_address": merge_address_lines(location["locale"]["address"]["addressLines"]),
                "city": location["locale"]["address"]["cityTown"],
                "postcode": location["locale"]["address"]["postalCode"],
                "state": location["locale"]["address"]["stateProvince"],
                "country": location["locale"]["address"]["countryCode"],
                "phone": location["phoneNumber"].get("raw"),
                "website": response.meta["url_map"][location["locationId"]],
                "branch": location["vanityName"],
                "operator": location["legalName"],
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
                yield from self.parse_departments(properties, location) or []
                apply_category(Categories.SHOP_SUPERMARKET, properties)

            yield Feature(**properties)

    def parse_departments(self, supermarket_properties, location) -> Iterable[Feature]:
        for department in location.get("departments"):
            cat = self.departments.get(department["code"])
            if not cat:
                continue

            properties = deepcopy(supermarket_properties)
            properties["ref"] += department["code"]
            properties["phone"] = department.get("phoneNumber", {}).get("raw")

            if department.get("locale"):
                properties["lat"] = department["locale"]["location"]["lat"]
                properties["lon"] = department["locale"]["location"]["lng"]
                properties["street_address"] = merge_address_lines(department["locale"]["address"]["addressLines"])
                properties["city"] = department["locale"]["address"]["cityTown"]
                properties["postcode"] = department["locale"]["address"]["postalCode"]
                properties["state"] = department["locale"]["address"]["stateProvince"]
                properties["country"] = department["locale"]["address"]["countryCode"]

            properties["opening_hours"] = self.parse_hours(department.get("prettyHours", []))

            apply_category(cat, properties)

            yield Feature(**properties)

    @staticmethod
    def parse_hours(rules: [dict]) -> OpeningHours:
        hours_string = ""
        for day_hours in rules:
            hours_string = "{} {}: {}".format(hours_string, day_hours["displayName"], day_hours["displayHours"])

        oh = OpeningHours()
        oh.add_ranges_from_string(hours_string)
        return oh
