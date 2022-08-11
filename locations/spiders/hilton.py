# -*- coding: utf-8 -*-
import scrapy
from locations.linked_data_parser import LinkedDataParser


def from_wikidata(name, code):
    return {"brand": name, "brand_wikidata": code}


class HiltonSpider(scrapy.spiders.SitemapSpider):
    name = "hilton"
    sitemap_urls = [
        "https://www.hilton.com/temporary/legacy-sitemap1.xml",
        "https://www.hilton.com/temporary/legacy-sitemap2.xml",
    ]
    download_delay = 0.2
    HILTON_TRU = from_wikidata("Tru by Hilton", "Q24907770")
    HILTON_WALDORF = from_wikidata("Waldorf Astoria", "Q3239392")
    HILTON_GARDEN = from_wikidata("Hilton Garden Inn", "Q1162859")
    HILTON_EMBASSY = from_wikidata("Embassy Suites", "Q5369524")
    HILTON_HOMEWOOD = from_wikidata("Homewood Suites by Hilton", "Q5890701")
    HILTON_HOME2 = from_wikidata("Home2 Suites by Hilton", "Q5887912")
    HILTON_DOUBLETREE = from_wikidata("DoubleTree by Hilton", "Q2504643")
    HILTON_CANOPY = from_wikidata("Canopy by Hilton", "Q30632909")
    HILTON_CONRAD = from_wikidata("Conrad Hotels & Resorts", "Q855525")
    HILTON_HAMPTON = from_wikidata("Hampton by Hilton", "Q5646230")
    HILTON_HOTELS = from_wikidata("Hilton Hotels & Resorts", "Q598884")
    # Looks like internally Hilton assign each hotel a 7-alpha code, the last
    # two letters of which indicate the brand.
    my_brands = {
        "ci": HILTON_CONRAD,
        "di": HILTON_DOUBLETREE,
        "dt": HILTON_DOUBLETREE,
        "es": HILTON_EMBASSY,
        "hf": HILTON_HOTELS,
        "hh": HILTON_HOTELS,
        "hi": HILTON_HOTELS,
        "hn": HILTON_HOTELS,
        "hs": HILTON_HOTELS,
        "ht": HILTON_HOME2,
        "hw": HILTON_HOMEWOOD,
        "hx": HILTON_HAMPTON,
        "gi": HILTON_GARDEN,
        "py": HILTON_CANOPY,
        "ru": HILTON_TRU,
        "tw": HILTON_HOTELS,
        "wa": HILTON_WALDORF,
    }

    def sitemap_filter(self, entries):
        # The sitemap URLs and the gymnastics on display here shows that the Hilton site
        # is in somewhat of a state of flux.
        for entry in entries:
            url = entry["loc"]
            if "curiocollection3" in url or "GV/" in url:
                continue
            if url.endswith("/about/index.html") or url.endswith("rooms/index.html"):
                hotel = url.split("/")[-3]
                splits = hotel.split("-")
                code = splits.pop().lower()
                splits.insert(0, code)
                if code == "dt":
                    # Some Doubletree links have XXXXX-DT rather than XXXXXDT codes.
                    code = splits.pop().lower()
                    splits.insert(0, code)
                entry["loc"] = "https://www.hilton.com/en/hotels/{}/".format(
                    "-".join(splits)
                )
                yield entry

    def lookup_brand(self, response):
        if "-dt-doubletree-" in response.url:
            # Catch the XXXXX-DT rather than XXXXXDT case
            return self.HILTON_DOUBLETREE
        splits = response.url.split("/")[-2]
        code = splits.split("-")[0][-2:]
        return self.my_brands.get(code)

    def parse(self, response):
        brand = self.lookup_brand(response)
        if brand:
            item = LinkedDataParser.parse(response, "Hotel")
            if item:
                item["ref"] = response.url
                item["brand"] = brand["brand"]
                item["brand_wikidata"] = brand["brand_wikidata"]
                # The street address is set by Hilton to be the full address of the property.
                # This can be fixed up rather well given that Hilton set the city field correctly.
                street_address = item["street_address"]
                splits = street_address.split(", {},".format(item["city"]))
                if len(splits) == 2:
                    item["addr_full"] = street_address
                    item["street_address"] = splits[0]
                return item
        else:
            self.logger.warn("unable to lookup brand: %s", response.url)
