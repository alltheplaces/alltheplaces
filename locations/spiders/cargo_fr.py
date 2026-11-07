import re

from scrapy.http import HtmlResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.items import Feature


class CargoFrSpider(SitemapSpider):
    """Spider for CarGo vehicle‑rental agencies in France.
    Data source: https://www.cargo.fr/sitemap.xml – agency pages under
    /les‑agences‑cargo/cargo-location-de‑vehicules-…
    """

    name = "cargo_fr"
    item_attributes = {
        "brand": "CarGo",
        "brand:wikidata": "Q117662226",
        "country": "FR",
        "source": "https://www.cargo.fr/les-agences-cargo/",
        "categories": Categories.CAR_RENTAL,
    }
    sitemap_urls = ["https://www.cargo.fr/sitemap.xml"]
    # Only crawl agency URLs
    sitemap_rules = [(r"/les‑agences‑cargo/cargo-location-de‑vehicules-.*", "parse_agency")]
    download_delay = 1.0

    def parse_agency(self, response: HtmlResponse):
        # Agency name – headline contains "CarGo" and location info
        name = response.css("h1.title::text").get(default="").strip()
        # Address – span with class "address"
        street_address = response.css("span.address::text").get(default="").strip()
        # Phone – text containing "Tél" or "T??l??phone"
        phone = (
            response.xpath("//div[contains(text(),'Tél') or contains(text(),'Téléphone')]/text()").re_first(
                r"(\d[\d\s]+)"
            )
            or ""
        ).strip()
        # Coordinates – hidden inputs use comma as decimal separator
        lat_raw = response.css("input#CityCoordinatesLat::attr(value)").get()
        lon_raw = response.css("input#CityCoordinatesLng::attr(value)").get()
        latitude = float(lat_raw.replace(",", ".")) if lat_raw else None
        longitude = float(lon_raw.replace(",", ".")) if lon_raw else None
        # Stable reference – hidden LocationId field
        ref = response.css("input#LocationId::attr(value)").get()
        # Opening hours – list items with day and schedule
        opening_hours = []
        day_map = {
            "lundi": "Mo",
            "mardi": "Tu",
            "mercredi": "We",
            "jeudi": "Th",
            "vendredi": "Fr",
            "samedi": "Sa",
            "dimanche": "Su",
        }
        for li in response.css("ul.m-0.mt-3.p-0 li"):
            day_fr = li.css("span.day::text").get(default="").strip().lower()
            schedule = li.css("span.schedule::text").get(default="").strip()
            if not schedule or "fermé" in schedule.lower():
                continue
            # Some schedules include a comma separating morning/afternoon
            parts = [s.strip() for s in schedule.split(",")]
            for part in parts:
                match = re.match(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})", part)
                if match:
                    opening_hours.append(
                        {
                            "day": day_map.get(day_fr, day_fr),
                            "open": match.group(1),
                            "close": match.group(2),
                        }
                    )
        # Build Feature item
        item = Feature(
            ref=ref,
            name=name,
            street_address=street_address,
            phone=phone,
            lat=latitude,
            lon=longitude,
            opening_hours=opening_hours,
        )
        yield self.wrap_item(item, response)
