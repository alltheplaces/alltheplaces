import urllib.parse

import scrapy

from locations.categories import Categories, PaymentMethods, apply_category, map_payment
from locations.items import Feature


# Hotels (including hostels and serviced apartments) in Switzerland
class DiscoverSwissSpider(scrapy.Spider):
    name = "discover_swiss"
    allowed_domains = ["api.discover.swiss"]
    headers = {
        "Ocp-Apim-Subscription-Key": "defe4e15094b4d388ecf3b37bbe88a85",
        "Accept-Language": "de",
    }
    url = "https://api.discover.swiss/info/v2/lodgingbusinesses/?project=dsod-content&top=-1"

    def start_requests(self):
        yield scrapy.Request(self.url, headers=self.headers)

    def parse(self, response):
        data = response.json()
        token = data.get("nextPageToken")
        if token and data.get("hasNextPage"):
            token_quoted = urllib.parse.quote(token, safe="")
            next_url = self.url + "&continuationToken=" + token_quoted
            yield scrapy.Request(next_url, headers=self.headers)
        for item in data.get("data", []):
            category = self.parse_category(item)
            ref = self.parse_ref(item)
            geo = item.get("geo")
            if item.get("removed") or not all([category, ref, geo]):
                continue
            address = item.get("address", {})
            extras = {
                "beds": item.get("numberOfBeds"),
                "ele": geo.get("elevation"),
                "rooms": self.parse_rooms(item),
                "stars": self.parse_stars(item),
            }
            feature = Feature(
                ref=ref,
                lat=geo["latitude"],
                lon=geo["longitude"],
                name=item["name"],
                street_address=address.get("streetAddress") or None,
                postcode=address.get("postalCode") or None,
                city=address.get("addressLocality") or None,
                country=address.get("addressCountry") or "CH",
                image=item.get("image", {}).get("contentUrl"),
                phone=item.get("telephone") or None,
                email=address.get("email") or None,
                website=item.get("url") or None,
                extras={k: str(v) for (k, v) in extras.items() if v},
            )
            apply_category(category, feature)
            self.parse_payment(item, feature)
            yield feature

    def parse_category(self, item):
        t = item.get("type")
        if t == "schema.org/LodgingBusiness":
            subtype = item.get("starRating", {}).get("additionalType")
            return {
                "ServicedApartments": Categories.TOURISM_APARTMENT,
                "swissLodge": Categories.TOURISM_HOSTEL,
            }.get(subtype, Categories.HOTEL)
        return None

    def parse_payment(self, item, feature):
        for p in item.get("paymentAccepted", "").split(","):
            # "Postcard" seems too Switzerland-specific to be added
            # to categories.py.
            p = {"Postcard": "PostFinance Card"}.get(p, p)
            map_payment(feature, p, PaymentMethods)

    def parse_ref(self, item):
        for prop in item.get("additionalProperty", []):
            if prop.get("propertyId") == "hsId":
                if value := prop.get("value"):
                    return str(value)
        return None

    def parse_rooms(self, item):
        for c in item.get("numberOfRooms", []):
            if c.get("propertyId") == "total":
                return c.get("value")
        return None

    def parse_stars(self, item):
        if s := item.get("starRating"):
            stars = str(s.get("ratingValue", "")).rstrip(".0")
            if s.get("superior"):
                stars = stars + "S"
            return stars
        return None
