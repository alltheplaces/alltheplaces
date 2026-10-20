import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# Placeholder phone number used as a template default when a store hasn't set a real one
PLACEHOLDER_PHONE = "0400000000"

HOUR_RE = re.compile(r"^\d{1,2}h\d{2}$")


class BoulangerieAngeSpider(SitemapSpider):
    name = "boulangerie_ange"
    item_attributes = {"brand": "Ange", "brand_wikidata": "Q98383422"}
    sitemap_urls = ["https://www.boulangerie-ange.fr/stores-sitemap.xml"]
    sitemap_rules = [(r"/stores/[^/]+/$", "parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["name"] = response.css("h1.details-header__title span::text").get(default="").strip() or None

        phone = response.css(".stores-card__phone .stores-card__txt::text").get(default="").strip()
        if phone and phone.replace(" ", "") != PLACEHOLDER_PHONE:
            item["phone"] = phone

        street = response.css(".stores-card__adress .stores-card__txt::text").get(default="").strip()
        city_line = " ".join(response.css(".stores-card__adress .stores-card__txt b::text").getall()).strip()
        item["addr_full"] = merge_address_lines([street, city_line]) or None

        if m := re.search(r"let lat\s*=\s*(-?[\d.]+);", response.text):
            item["lat"] = m.group(1)
        if m := re.search(r"let lng\s*=\s*(-?[\d.]+);", response.text):
            item["lon"] = m.group(1)

        # The store finder covers France (incl. overseas departments) and Canada (Quebec), but
        # the whole site lives under the .fr TLD, so the country can't be inferred from the URL.
        # Quebec stores use "QC"/Canadian postcodes; a few lack an address entirely, so fall back
        # to longitude (Quebec is far west of any French territory covered here).
        if re.search(r"[A-Za-z]\d[A-Za-z]\s*\d[A-Za-z]\d", item["addr_full"] or "") or ", QC" in (
            item["addr_full"] or ""
        ):
            item["country"] = "CA"
        elif item.get("lon") is not None and float(item["lon"]) < -50:
            item["country"] = "CA"
        else:
            item["country"] = "FR"

        item["opening_hours"] = OpeningHours()
        for row in response.css("table.horaires tr"):
            day = sanitise_day(row.css("th::text").get(), DAYS_FR)
            start = row.css("td.s::text").get(default="").strip()
            end = row.css("td.e::text").get(default="").strip()
            if not day or not HOUR_RE.match(start) or not HOUR_RE.match(end):
                continue
            item["opening_hours"].add_range(day, start.replace("h", ":"), end.replace("h", ":"))

        apply_category(Categories.SHOP_BAKERY, item)

        yield item
