import json

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.items import GeojsonPointItem


class MigrosCHSpider(SitemapSpider):
    name = "migros_ch"
    brands = {
        "alna": ("Alnatura", "Q876811", {"shop": "supermarket"}),
        "chng": ("Migros Change", "Q115659823", {"amenity": "bureau_de_change"}),
        "cof": (
            "Migros Café",
            "Q115661379",
            {"amenity": "cafe", "cuisine": "coffee_shop"},
        ),
        "doi": ("Do It + Garden", "Q108866119", {"shop": "doityourself"}),
        "flori": ("Florissimo", "Q115659418", {"shop": "florist"}),
        "gour": ("Migros Take Away", "Q111826610", {"amenity": "fast_food"}),
        "mec": ("melectronics", "Q110276002", {"shop": "electronics"}),
        "mica": ("Micasa", "Q1926676", {"shop": "furniture"}),
        "mno": ("Migrolino", "Q56745088", {"shop": "convenience"}),
        "mp": ("Migros Partner", "Q115661515", {"shop": "supermarket"}),
        "obi": ("OBI", "Q300518", {"shop": "doityourself"}),
        "out": ("Outlet Migros", "Q115659564", {"shop": "supermarket"}),
        "pickmup_247pmubox": (
            "PickMup Box",
            "Q115679275",
            {"amenity": "product_pickup", "opening_hours": "24/7"},
        ),
        "res": ("Migros Restaurant", "Q111803848", {"amenity": "restaurant"}),
        "super": ("Migros", "Q115661152", {"shop": "supermarket"}),
        "spx": ("SportXX", "Q19309319", {"shop": "sports"}),
        "voi": ("VOI", "Q110277616", {"shop": "supermarket"}),
    }
    allowed_domains = ["filialen.migros.ch"]
    sitemap_urls = ["https://filialen.migros.ch/sitemap.xml"]
    sitemap_follow = ["/de/"]
    sitemap_rules = [(r"https://filialen\.migros\.ch/de/", "parse")]

    def parse(self, response):
        data_js = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        data = json.loads(data_js)
        page_props = data["props"]["pageProps"]
        store = page_props["initialActiveStore"]
        loc = store["location"]
        for market in store["markets"]:
            if market["slug"] != page_props["initialSlug"]:
                continue
            brand, brand_wikidata, brand_extras = self.brands.get(market["type"], (None, None, {}))
            extras = {
                "start_date": market.get("opening_date"),
                "end_date": market.get("closing_date"),
            }
            extras = {k: v for k, v in extras.items() if v}
            props = {
                "brand": brand,
                "brand_wikidata": brand_wikidata,
                "city": loc["city"],
                "country": loc["country"],
                "email": market["email"],
                "extras": extras,
                "lat": loc["geo"]["lat"],
                "lon": loc["geo"]["lon"],
                "name": brand,
                "opening_hours": self.parse_opening_hours(market),
                "phone": market.get("phone"),
                "postcode": loc.get("zip"),
                "ref": market["id"],
                "street_address": loc.get("address"),
                "website": response.url,
            }
            extras.update(brand_extras)
            if oh := extras.pop("opening_hours", None):
                props["opening_hours"] = oh
            yield GeojsonPointItem(**props)

    @staticmethod
    def parse_opening_hours(market):
        oh = OpeningHours()
        for o in market.get("opening_hours", []):
            if o.get("active"):
                for hours in o.get("opening_hours", []):
                    day = DAYS[hours["day_of_week"] - 1]
                    for i in range(5):
                        open_time = hours.get("time_open%d" % i)
                        close_time = hours.get("time_close%d" % i)
                        if open_time and close_time:
                            oh.add_range(day, open_time, close_time)
        return oh.as_opening_hours()
