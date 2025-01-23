import json
import re

import chompjs
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MigrosCHSpider(SitemapSpider):
    name = "migros_ch"
    brands = {
        "alna": ("Alnatura", "Q876811", Categories.SHOP_SUPERMARKET),
        "chng": ("Migros Change", "Q115659823", Categories.BUREAU_DE_CHANGE),
        "cof": ("Migros Café", "Q115661379", Categories.COFFEE_SHOP),
        "doi": ("Do It + Garden", "Q108866119", Categories.SHOP_DOITYOURSELF),
        "flori": ("Florissimo", "Q115659418", Categories.SHOP_FLORIST),
        "gour": ("Migros Take Away", "Q111826610", Categories.FAST_FOOD),
        "mec": ("melectronics", "Q110276002", Categories.SHOP_ELECTRONICS),
        "mica": ("Micasa", "Q1926676", Categories.SHOP_FURNITURE),
        "mno": ("Migrolino", "Q56745088", Categories.SHOP_CONVENIENCE),
        "mp": ("Migros Partner", "Q115661515", Categories.SHOP_SUPERMARKET),
        "obi": ("OBI", "Q300518", Categories.SHOP_DOITYOURSELF),
        "out": ("Outlet Migros", "Q115659564", Categories.SHOP_SUPERMARKET),
        "pickmup": ("PickMup Box", "Q115679275", Categories.PRODUCT_PICKUP),
        "res": ("Migros Restaurant", "Q111803848", Categories.RESTAURANT),
        "super": ("Migros", "Q115661152", Categories.SHOP_SUPERMARKET),
        "spx": ("SportXX", "Q19309319", Categories.SHOP_SPORTS),
        "voi": ("VOI", "Q110277616", Categories.SHOP_SUPERMARKET),
    }
    obsolete_brands = {"mod"}
    allowed_domains = ["filialen.migros.ch"]
    sitemap_urls = ["https://filialen.migros.ch/sitemap.xml"]
    sitemap_follow = ["/de/"]
    sitemap_rules = [(r"https://filialen\.migros\.ch/de/", "parse")]

    def parse(self, response):

        data = json.loads(re.search(r'({.*})\]n',response.xpath('//*[contains(text(),"initialActiveStore")]/text()').get().replace('\\',"")).group(1))
        store = data["initialActiveStore"]
        loc = store["location"]
        for market in store["markets"]:
            if market["slug"] != data["initialSlug"]:
                continue
            brand_key = market["type"].split("_")[0]
            if brand_key not in self.brands:
                if brand_key not in self.obsolete_brands:
                    self.logger.error('unknown brand: "%s"' % brand_key)
                continue
            brand, brand_wikidata, category = self.brands[brand_key]
            extras = {
                "start_date": market.get("opening_date"),
                "end_date": market.get("closing_date"),
            }
            item = Feature(
                brand=brand,
                brand_wikidata=brand_wikidata,
                city=loc["city"],
                country=loc["country"],
                email=market["email"],
                extras={k: v for k, v in extras.items() if v},
                lat=loc["geo"]["lat"],
                lon=loc["geo"]["lon"],
                name=brand,
                opening_hours=self.parse_opening_hours(market),
                phone=market.get("phone"),
                postcode=loc.get("zip"),
                ref=market["id"],
                street_address=loc.get("address"),
                website=response.url,
            )
            apply_category(category, item)
            yield item

    @staticmethod
    def parse_opening_hours(market):
        if market["type"] == "pickmup_247pmubox":
            return "24/7"
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
