from html import unescape

from chompjs import parse_js_object
from scrapy import Selector
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class WLaneAUSpider(SitemapSpider):
    name = "w_lane_au"
    item_attributes = {"brand": "W Lane", "brand_wikidata": "Q120645873"}
    allowed_domains = ["www.wlane.com.au"]
    sitemap_urls = ["https://www.wlane.com.au/Store.xml"]
    sitemap_rules = [(r"\/stores\/(?!nz\/)", "parse")] # NZ location is not open to the public

    def parse(self, response):
        ldjsontext = (
            response.xpath('//script[contains(text(), "application/ld+json")]/text()')
            .get()
            .split("JSON.stringify(", 1)[1]
            .split(");", 1)[0]
            .replace("controls.storeFinder.formatedSchemaOpeningHour(", "")
            .replace("),", ",")
            .strip()
        )
        ldjson = parse_js_object(ldjsontext)
        properties = {
            "ref": response.url,
            "name": ldjson["name"],
            "lat": ldjson["geo"]["latitude"],
            "lon": ldjson["geo"]["longitude"],
            "street_address": unescape(ldjson["address"]["streetAddress"]).strip(),
            "city": ldjson["address"]["addressLocality"],
            "state": ldjson["address"]["addressRegion"],
            "phone": ldjson["telephone"],
            "website": response.url,
        }
        hours_text = " ".join(Selector(text=ldjson["openingHours"]).xpath("//text()").getall())
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_text)
        yield Feature(**properties)
