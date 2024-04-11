from pathlib import Path
from urllib.parse import urlparse

import geonamescache
import scrapy
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import CHROME_LATEST


class HiltonSpider(SitemapSpider, StructuredDataSpider):
    name = "hilton"
    sitemap_urls = ["https://www.hilton.com/sitemap.xml"]
    custom_settings = {
        "USER_AGENT": CHROME_LATEST,
        "DOWNLOAD_DELAY": 0.2,
    }
    visited_pages = set()

    HILTON_DOUBLETREE = ["DoubleTree by Hilton", "Q2504643"]
    HILTON_HOTELS = ["Hilton Hotels & Resorts", "Q598884"]
    # Each hotel has a 7 digit alpha code, the last two letters indicate the brand.
    my_brands = {
        "ci": ["Conrad Hotels & Resorts", "Q855525"],
        "di": HILTON_DOUBLETREE,
        "dt": HILTON_DOUBLETREE,
        "es": ["Embassy Suites", "Q5369524"],
        "gi": ["Hilton Garden Inn", "Q1162859"],
        "he": HILTON_HOTELS,
        "hf": HILTON_HOTELS,
        "hh": HILTON_HOTELS,
        "hi": HILTON_HOTELS,
        "hn": HILTON_HOTELS,
        "hs": HILTON_HOTELS,
        "ht": ["Home2 Suites by Hilton", "Q5887912"],
        "hw": ["Homewood Suites by Hilton", "Q5890701"],
        "hx": ["Hampton by Hilton", "Q5646230"],
        "ol": ["LXR Hotels & Resorts", "Q64605184"],
        "on": HILTON_HOTELS,
        "pe": HILTON_HOTELS,
        "po": ["Tempo by Hilton", "Q112144357"],
        "pr": "Hilton Hotels & Resorts",
        "py": ["Canopy by Hilton", "Q30632909"],
        "qq": "Curio Collection",
        "ru": ["Tru by Hilton", "Q24907770"],
        "tw": HILTON_HOTELS,
        "ua": ["Motto by Hilton", "Q112144350"],
        "up": "Tapestry Collection",
        "wa": ["Waldorf Astoria", "Q3239392"],
    }
    gc = geonamescache.GeonamesCache()
    requires_proxy = True

    def _parse_sitemap(self, response):
        for x in super()._parse_sitemap(response):
            if x.url.endswith(".xml"):
                yield x
            elif x.url.endswith("/hotel-info/"):
                hotel_url = x.url.replace("/hotel-info/", "/")
                hotel_name = Path(urlparse(hotel_url).path).name

                if hotel_name in self.visited_pages:
                    # There are localized pages for each hotel, don't scrape same hotel twice.
                    continue

                yield scrapy.Request(hotel_url, callback=self.parse_sd)
                self.visited_pages.add(hotel_name)

    def lookup_brand(self, response):
        if "-dt-doubletree-" in response.url:
            # Catch the XXXXX-DT rather than XXXXXDT case
            return self.HILTON_DOUBLETREE
        splits = response.url.split("/")[-2]
        code = splits.split("-")[0][-2:]
        return self.my_brands.get(code)

    def post_process_item(self, item, response, ld_data, **kwargs):
        if brand := self.lookup_brand(response):
            if isinstance(brand, str):
                return

            # Last part of url is unique
            item["ref"] = Path(urlparse(response.url).path).name
            # Website provided in structured data does not work, so replace it with working url
            item["website"] = response.url

            item["brand"], item["brand_wikidata"] = brand
            # In many cases the street address is set by Hilton to be the full address
            # of the property. A certain amount of fixup can be attempted.
            street_address = item["street_address"]
            splits = street_address.split(", {},".format(item["city"]))
            if len(splits) == 2:
                item["addr_full"] = street_address
                item["street_address"] = splits[0]
            else:
                # If we find the country name in the street address treat it as a full address.
                # Otherwise for those few remaining countries we will leave as a street address
                # which at time of writing is totally correct.
                country = self.gc.get_countries().get(item["country"])
                if country and country["name"].lower() in street_address.lower():
                    item["addr_full"] = street_address
                    item["street_address"] = None
            yield item
        else:
            self.logger.error("unable to lookup brand: %s", response.url)
