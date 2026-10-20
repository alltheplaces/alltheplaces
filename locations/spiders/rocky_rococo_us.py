import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature


class RockyRococoUSSpider(SitemapSpider):
    name = "rocky_rococo_us"
    item_attributes = {"brand": "Rocky Rococo", "brand_wikidata": "Q7356002"}
    allowed_domains = ["rockyrococo.com"]
    sitemap_urls = ["https://rockyrococo.com/sitemap_index.xml"]
    sitemap_rules = [(r"/locations/[^/]+/$", "parse")]

    def parse(self, response):
        h1 = response.xpath("//h1//text()").get()
        if not h1 or "–" not in h1:
            return
        city_state, branch = (s.strip() for s in h1.split("–", 1))
        city, state = (s.strip() for s in city_state.split(",", 1))

        addr_full = " ".join(
            t.strip()
            for t in response.xpath(
                '//div[@class="elementor-icon-box-content"][.//span[normalize-space()="Address"]]'
                '/p[@class="elementor-icon-box-description"]//text()'
            ).getall()
            if t.strip()
        )

        item = Feature()
        item["ref"] = item["website"] = response.url
        item["city"] = city
        item["state"] = state
        # Street addresses don't reliably split from the "Suite"/"#" portion, so only
        # split off city/postcode (both cross-checked against the page heading) and
        # keep the rest as street_address; fall back to addr_full if that fails.
        if (idx := addr_full.find(f"{city},")) > 0:
            item["street_address"] = addr_full[:idx].strip()
            if postcode_match := re.search(r"(\d{5})$", addr_full):
                item["postcode"] = postcode_match.group(1)
        else:
            item["addr_full"] = addr_full

        item["branch"] = branch
        item["name"] = self.item_attributes["brand"]

        # Coordinates and phone are most reliably found in the Elementor page config's
        # "excerpt" JS string, which embeds a Google Maps "Get Directions" link with an
        # @lat,lng and a tel: link even on pages where the og:description meta tag omits them.
        if excerpt_match := re.search(r'"excerpt":"(.*?)","featuredImage"', response.text):
            excerpt = json.loads(f'"{excerpt_match.group(1)}"')
            if maps_match := re.search(r'href="(https://www\.google\.com/maps/place/[^"]+)"', excerpt):
                lat, lon = url_to_coords(maps_match.group(1))
                if (lat, lon) == (44.2681059, -88.4709387) and city != "Appleton":
                    # The site has a copy/paste bug: several unrelated location pages link to
                    # the same Google Maps place (the Appleton "Fox River Mall" store, where
                    # this coordinate is correct). Drop it elsewhere rather than mis-locate the pin.
                    lat = lon = None
                item["lat"], item["lon"] = lat, lon
            if tel_match := re.search(r'href="tel:(\+?\d+)"', excerpt):
                item["phone"] = tel_match.group(1)

        if phone := response.xpath('//span[@class="elementor-icon-list-text"][contains(., "Call Us")]/text()').re_first(
            r"Call Us\s+(.+)"
        ):
            item["phone"] = phone

        item["opening_hours"] = OpeningHours()
        hours_text = " ".join(
            t.strip()
            for t in response.xpath(
                '//div[@class="elementor-icon-box-content"][.//span[normalize-space()="Hours"]]'
                '/p[@class="elementor-icon-box-description"]//text()'
            ).getall()
            if t.strip()
        )
        item["opening_hours"].add_ranges_from_string(hours_text)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"

        yield item
