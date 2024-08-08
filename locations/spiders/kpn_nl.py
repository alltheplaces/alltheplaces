import scrapy

from locations.categories import Categories
from locations.hours import DAYS_NL, OpeningHours
from locations.items import Feature


class KpnNLSpider(scrapy.Spider):
    name = "kpn_nl"
    start_urls = ["https://www.kpn.com/w3/rest/storelocator/stores"]

    item_attributes = {"brand": "KPN", "brand_wikidata": "Q338633", "extras": Categories.SHOP_MOBILE_PHONE.value}
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"referer": "https://www.kpn.com/w3/vind-een-winkel/"},
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response, **kwargs):
        for store in response.json().get("stores"):
            oh = OpeningHours()
            for day in DAYS_NL.keys():
                if not store.get(f"{day.lower()}_open"):
                    continue
                open = store.get(f"{day.lower()}_open")
                close = store.get(f"{day.lower()}_dicht")
                oh.add_range(day=DAYS_NL.get(day), open_time=open, close_time=close, time_format="%H:%M")
            coordinates = store.get("locatie")
            yield Feature(
                {
                    "ref": store.get("winkelnummer"),
                    "name": store.get("formulenaam"),
                    "street": store.get("straat"),
                    "housenumber": store.get("huisnummer"),
                    "phone": store.get("phone"),
                    "email": store.get("email"),
                    "postcode": store.get("postcode"),
                    "city": store.get("plaats"),
                    "website": f"https://www.kpn.com{store.get('link')}",
                    "lat": coordinates.get("lat"),
                    "lon": coordinates.get("lng"),
                    "opening_hours": oh,
                }
            )
