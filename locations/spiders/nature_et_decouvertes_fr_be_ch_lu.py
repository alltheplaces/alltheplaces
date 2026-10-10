import re
from typing import Any
from urllib.parse import urlsplit

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature

# The URL path segment following "/magasins/" is a French department name (or a
# city-based slug) for French stores, but names the country for these three
# neighbouring countries where Nature & Découvertes also trades.
COUNTRY_URL_SEGMENTS = {"belgique": "BE", "suisse": "CH", "luxembourg": "LU"}


class NatureEtDecouvertesFRBECHLUSpider(SitemapSpider):
    name = "nature_et_decouvertes_fr_be_ch_lu"
    item_attributes = {"brand": "Nature & Découvertes", "brand_wikidata": "Q3337111"}
    sitemap_urls = ["https://www.natureetdecouvertes.com/sitemaps/sitemap-magasins.xml"]
    sitemap_rules = [(r"/magasins/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        branch = response.css(".breadcrumbs__ariane a:last-child::attr(title)").get()
        if not branch:
            # Pages such as "/magasins/test" carry none of the store markup below.
            return

        path_segments = urlsplit(response.url).path.strip("/").split("/")  # ["magasins", region_or_slug, ...]

        item = Feature()
        item["ref"] = "/".join(path_segments[1:])
        item["branch"] = branch
        item["website"] = response.url
        item["country"] = COUNTRY_URL_SEGMENTS.get(path_segments[1], "FR")

        address_lines = [line.strip() for line in response.css("address.shop-address::text").getall() if line.strip()]
        if address_lines and " - " in address_lines[-1]:
            item["street_address"] = " ".join(address_lines[:-1])
            item["postcode"], item["city"] = (part.strip() for part in address_lines[-1].split(" - ", 1))
        elif address_lines:
            item["street_address"] = " ".join(address_lines)

        item["phone"] = response.xpath('//li[contains(., "Tél")]//a/text()').get()

        oh = OpeningHours()
        for row in response.css("ul.shop-opening-list li"):
            day = DAYS_FR.get(row.xpath("./span[1]/text()").get("").strip(" :"))
            hours = (row.css("span.shop-hours::text").get() or "").strip()
            if not day or not hours:
                continue
            if "eclipse" in hours.lower():
                oh.set_closed(day)
            else:
                # Most pages use "09:30–20:00"; some instead use the French "de 10h00 à 19h00" form.
                times = re.findall(r"\d{1,2}:\d{2}", re.sub(r"(\d{1,2})h(\d{2})", r"\1:\2", hours))
                if len(times) == 2:
                    oh.add_range(day, times[0], times[1])
        item["opening_hours"] = oh

        extract_google_position(item, response)

        apply_category(Categories.SHOP_OUTDOOR, item)

        yield item
