import re
from urllib.parse import urlparse

import scrapy
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# Brand naming (and the matching NSI entries under brand_wikidata Q303439) varies by
# storefront domain:
#  - legolanddiscoverycentre.com -> "LEGOLAND Discovery Centre" (AU, CA, DE, GB, NL, TR, HK)
#  - legolanddiscoverycenter.com -> "LEGOLAND Discovery Center" (US, JP, CN)
#  - legodiscoverycenter.com     -> "LEGO Discovery Center" (US legacy sites, e.g. Boston, Atlanta)
BRAND_BY_HOST = {
    "legolanddiscoverycentre.com": "LEGOLAND Discovery Centre",
    "legolanddiscoverycenter.com": "LEGOLAND Discovery Center",
    "legodiscoverycenter.com": "LEGO Discovery Center",
}


class LegolandDiscoveryCentreSpider(SitemapSpider, StructuredDataSpider):
    name = "legoland_discovery_centre"
    item_attributes = {"brand_wikidata": "Q303439"}
    sitemap_urls = [
        "https://www.legolanddiscoverycentre.com/sitemap.xml",
        "https://www.legolanddiscoverycenter.com/sitemap.xml",
    ]
    # Only the canonical single-segment location root URLs, e.g. "/arizona/",
    # skipping locale-index and marketing pages, and per-location subpages
    # (which duplicate the same structured data under many URLs).
    sitemap_rules = [(r"^https://[^/]+/[a-z0-9-]+/$", "parse_sd")]
    wanted_types = ["TouristAttraction", "AmusementPark"]
    time_format = "%I:%M %p"

    async def start(self):
        async for request in super().start():
            yield request
        # Boston and Atlanta are live but have dropped out of the sitemap.
        for url in ["https://www.legodiscoverycenter.com/boston/", "https://www.legodiscoverycenter.com/atlanta/"]:
            yield scrapy.Request(url, callback=self.parse_sd)

    def pre_process_data(self, ld_data: dict, **kwargs):
        for obj in ld_data.values():
            if not isinstance(obj, dict):
                continue
            if t := obj.get("@type"):
                if isinstance(t, list) and len(t) == 1:
                    obj["@type"] = t[0]
            # A handful of pages append a trailing "°" to lat/lon values.
            for key in ["latitude", "longitude"]:
                if isinstance(obj.get(key), str):
                    obj[key] = obj[key].strip().rstrip("°")

    def post_process_item(self, item, response, ld_data, **kwargs):
        host = urlparse(response.url).netloc.removeprefix("www.")
        if host == "legolanddiscoverycentre.com" and "/hong-kong/" in response.url:
            item["brand"] = "樂高探索中心 LEGOLAND Discovery Centre"
        else:
            item["brand"] = BRAND_BY_HOST.get(host)
        apply_category(Categories.TOURISM_THEME_PARK, item)

        # Some pages fold the state into addressLocality, e.g. "Atlanta, GA".
        if city := item.get("city"):
            city = city.strip().rstrip(",").strip()
            if m := re.match(r"^(.+),\s*([A-Z]{2,3})$", city):
                city = m.group(1).strip()
                if not item.get("state"):
                    item["state"] = m.group(2)
            item["city"] = city

        # Dutch postcodes ("2586 JK") get mis-split, leaving the letters stuck
        # to the start of addressLocality instead, e.g. postcode "2586 " and
        # addressLocality " JK Den Haag,".
        if (postcode := item.get("postcode")) and (city := item.get("city")):
            if re.fullmatch(r"\d{4}", postcode.strip()) and (m := re.match(r"^([A-Z]{2})\s+(.+)$", city)):
                item["postcode"] = f"{postcode.strip()} {m.group(1)}"
                item["city"] = m.group(2)

        yield item
