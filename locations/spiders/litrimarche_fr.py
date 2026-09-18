import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class LitrimarcheFRSpider(scrapy.Spider):
    name = "litrimarche_fr"
    item_attributes = {"brand": "Litrimarché", "brand_wikidata": "Q127446387"}
    allowed_domains = ["litrimarche.fr"]
    start_urls = ["https://www.litrimarche.fr/magasins2"]

    def parse(self, response):
        for article in response.css("article.store-item"):
            ref = article.attrib["id"].removeprefix("store-")

            address_lines = [line.strip() for line in article.css("address::text").getall() if line.strip()]
            if not (m := re.match(r"^(\d{5})\s+(.+)$", address_lines[-2])):
                continue
            postcode, city = m.groups()

            footer_text = article.css(".store-item-footer li::text").getall()
            name = article.css(".card-title::text").get("").strip()

            item = Feature()
            item["ref"] = ref
            # Source data spells the brand prefix inconsistently: "LITRIMARCHÉ", "LITRIMARCHE"
            # (no accent), and "Litrimarché" all occur across the 101 store names.
            branch = re.sub(r"^LITRIMARCH[EÉ]\s*", "", name.upper())
            item["branch"] = branch.strip().title()
            street_address = ", ".join(address_lines[:-2])
            # Street text is usually already properly cased; a handful of stores give it
            # in all caps instead, so only re-case those rather than mangling the rest.
            item["street_address"] = street_address.title() if street_address.isupper() else street_address
            item["postcode"] = postcode
            item["city"] = city.title()
            item["country"] = "FR"
            item["phone"] = footer_text[0].strip() if len(footer_text) > 0 else None
            item["email"] = footer_text[1].strip() if len(footer_text) > 1 else None
            item["opening_hours"] = self.parse_hours(article)

            apply_category(Categories.SHOP_BED, item)

            # The URL slug needs hyphens where the address text has spaces (e.g.
            # "SAINT PRIEST EN JAREZ" 404s, "SAINT-PRIEST-EN-JAREZ" doesn't).
            store_url = response.urljoin(f"/store/{ref}-{postcode}-{city.replace(' ', '-')}")
            yield scrapy.Request(store_url, callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response, item):
        # /magasins2 already has name/address/phone/hours; this follow-up request
        # only exists because that page has no coordinates, unlike this JSON-LD.
        if ld_item := LinkedDataParser.parse(response, "LocalBusiness"):
            item["lat"] = ld_item.get("lat")
            item["lon"] = ld_item.get("lon")
        item["website"] = response.url
        yield item

    def parse_hours(self, article):
        oh = OpeningHours()
        for row in article.css("table tr"):
            day = sanitise_day(row.css("th::text").get(""), DAYS_FR)
            if not day:
                continue

            text = " ".join(row.css("td li::text").getall()).strip()
            if not text or text.lower() == "fermé":
                oh.set_closed(day)
                continue

            # Source data has occasional typos with a stray space before "h" or
            # between the two digits of an hour (e.g. "19 h", "1 2h").
            text = re.sub(r"(\d)\s+h\b", r"\1h", text)
            text = re.sub(r"(\d)\s+(\d)h", r"\1\2h", text)

            times = re.findall(r"(\d{1,2})h(\d{2})?", text)
            for (open_h, open_m), (close_h, close_m) in zip(times[0::2], times[1::2]):
                open_time = f"{int(open_h):02d}:{open_m or '00'}"
                close_time = f"{int(close_h):02d}:{close_m or '00'}"
                oh.add_range(day, open_time, close_time)

        return oh
