# -*- coding: utf-8 -*-
import json

from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem


class WesternUnionSpider(SitemapSpider):
    name = "western_union"
    item_attributes = {"brand": "Western Union", "brand_wikidata": "Q861042"}
    allowed_domains = ["location.westernunion.com", "locations.westernunion.com"]
    # Use plural, singular responds with a redirect confusing to scrapy?
    sitemap_urls = ["https://locations.westernunion.com/robots.txt"]
    sitemap_rules = [(r"westernunion\.com/.*/.*", "parse")]

    def sitemap_filter(self, entries):
        for entry in entries:
            if "/search/" in entry["loc"]:
                continue
            elif "/sitemap" in entry["loc"]:
                yield entry
            else:
                # Location pages redirect to singular, get ahead of them here.
                entry["loc"] = (
                    entry["loc"]
                    .replace("http://", "https://")
                    .replace("locations.westernunion.com", "location.westernunion.com")
                )
                yield entry

    def parse(self, response):
        script = response.css('script#__NEXT_DATA__[type="application/json"]::text')
        data = json.loads(script.get())
        store = data["props"]["initialState"]["locationDetails"]

        if store.keys() == {"error"}:
            # Location appears somehow defunct
            return

        # Note: There's also store.latitude and store.longitude as numbers,
        # except occasionally store.latitude == 80 for some reason, so
        # store.location seems slightly more reasonable. Except sometimes it
        # contains numbers multiplied by 10? But not consistently so, sometimes
        # just one ordinal or the other. Generally that causes obviously bogus
        # coordinates, namely |lat| > 90, |lon| > 180, which is a good thing
        # here so they can be discarded.
        lat, lon = map(float, store["location"].split(","))

        properties = {
            "lat": lat,
            "lon": lon,
            "name": store["name"],
            "ref": store["id"],
            "website": "https://location.westernunion.com/" + store["detailsUrl"],
            "street_address": store["streetAddress"],
            "city": store["city"],
            "state": store["state"],
            "postcode": store["postal"],
            "country": store["country"],
            "phone": store["phone"],
        }
        yield GeojsonPointItem(**properties)
