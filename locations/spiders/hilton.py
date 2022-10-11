# -*- coding: utf-8 -*-
import scrapy
import geonamescache
from locations.structured_data_spider import StructuredDataSpider


class HiltonSpider(scrapy.spiders.SitemapSpider, StructuredDataSpider):
    name = "hilton"
    sitemap_urls = ["https://www.hilton.com/sitemap.xml"]
    download_delay = 0.2

    HILTON_DOUBLETREE = ["DoubleTree by Hilton", "Q2504643"]
    HILTON_HOTELS = ["Hilton Hotels & Resorts", "Q598884"]
    # Each hotel has a 7 digit alpha code, the last two letters indicate the brand.
    my_brands = {
        "ci": ["Conrad Hotels & Resorts", "Q855525"],
        "di": HILTON_DOUBLETREE,
        "dt": HILTON_DOUBLETREE,
        "es": ["Embassy Suites", "Q5369524"],
        "hf": HILTON_HOTELS,
        "hh": HILTON_HOTELS,
        "hi": HILTON_HOTELS,
        "hn": HILTON_HOTELS,
        "hs": HILTON_HOTELS,
        "ht": ["Home2 Suites by Hilton", "Q5887912"],
        "hw": ["Homewood Suites by Hilton", "Q5890701"],
        "hx": ["Hampton by Hilton", "Q5646230"],
        "gi": ["Hilton Garden Inn", "Q1162859"],
        "ol": ["LXR Hotels & Resorts", "Q64605184"],
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

    def _parse_sitemap(self, response):
        for x in super()._parse_sitemap(response):
            if x.url.endswith(".xml"):
                yield x
            elif x.url.endswith("/hotel-info/"):
                yield scrapy.Request(x.url.replace("/hotel-info/", "/"), callback=self.parse_sd)

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
            item["ref"] = response.url
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
