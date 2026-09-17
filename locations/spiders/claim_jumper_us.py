import chompjs
from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class ClaimJumperUSSpider(Spider):
    name = "claim_jumper_us"
    item_attributes = {"brand": "Claim Jumper", "brand_wikidata": "Q5125081", "country": "US"}
    allowed_domains = ["www.claimjumper.com"]
    start_urls = ["https://www.claimjumper.com/store-locator/"]
    requires_proxy = True

    def parse(self, response):
        cache = chompjs.parse_js_object(response.text.split("window.__POPMENU_SSR_CACHE__ =", 1)[1])
        locations = next(value for key, value in cache.items() if key.startswith("restaurantWithLocationsQuery:"))

        for location in locations["restaurant"]["locations"]:
            if not location["isLocationEnabled"] or location["isLocationClosed"] or location["country"] != "US":
                continue

            detail_url = Selector(text=location["customLocationContent"]).css("a.location-info-hours::attr(href)").get()
            item = Feature(
                ref=location["slug"],
                name=self.item_attributes["brand"],
                branch=location["name"],
                lat=location["lat"],
                lon=location["lng"],
                street_address=location["streetAddress"],
                city=location["city"],
                state=location["state"],
                postcode=location["postalCode"],
                phone=location["phone"],
                website=response.urljoin(detail_url) if detail_url else None,
            )

            hours = OpeningHours()
            for line in location["schemaHours"]:
                hours.add_ranges_from_string(line)
            if hours.as_opening_hours():
                item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)
            yield item
