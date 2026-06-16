import re

from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class HousePLSpider(Spider):
    """Spider for House clothing stores in Poland and Europe.

    Closes #5930
    """

    name = "house_pl"
    item_attributes = {
        "brand": "House",
        "brand_wikidata": "Q9294202",
    }
    start_urls = ["https://www.housebrand.com/pl/pl/ajx/stores/all/"]

    def parse(self, response):
        kml_url = response.json()["content"]["kml_url"]
        if kml_url.startswith("//"):
            kml_url = "https:" + kml_url
        yield response.follow(kml_url, callback=self.parse_kml)

    def parse_kml(self, response):
        selector = Selector(
            text=response.body.decode().replace('xmlns="http://www.opengis.net/kml/2.2"', ""),
            type="xml",
        )
        for placemark in selector.xpath("//Placemark"):
            item = Feature()
            apply_category(Categories.SHOP_CLOTHES, item)

            name = placemark.xpath("name/text()").get("").strip()
            item["branch"] = name.removeprefix("HOUSE").strip()
            item["ref"] = re.sub(r"\s+", "-", name).casefold()

            lon, lat, _ = placemark.xpath("Point/coordinates/text()").get().split(",")
            item["lon"] = lon.strip()
            item["lat"] = lat.strip()

            description_html = placemark.xpath("description/text()").get("")
            desc = Selector(text=description_html)
            paras = desc.xpath("//p/text()").getall()

            # Description structure (empty <p> skipped by text() selector):
            # 0: street address
            # 1: city
            # 2: country (e.g. "Polska")
            # 3: gender labels (e.g. "ONA ON")
            # 4+: opening hours in Polish (e.g. "Pn.-Pt. 09:00-21:00")
            if len(paras) >= 2:
                item["street_address"] = paras[0]
                item["city"] = paras[1]
            if len(paras) >= 3 and paras[2] not in ("Polska", "Poland", ""):
                item["country"] = paras[2]
            else:
                item["country"] = "PL"

            hours_strings = [p for p in paras[4:] if p.strip()]
            if hours_strings:
                oh = OpeningHours()
                oh.add_ranges_from_string(", ".join(hours_strings), days=DAYS_PL)
                item["opening_hours"] = oh

            yield item
