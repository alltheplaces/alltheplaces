from html import unescape

from chompjs import parse_js_object
from scrapy import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature


class MosaicBrandSpider(CrawlSpider):
    name = "mosaic_brands"
    allowed_domains = [
        "www.autographfashion.com.au",
        "www.katies.com.au",
        "www.millers.com.au",
        "www.nonib.com.au",
        "www.rivers.com.au",
        "www.rockmans.com.au",
    ]
    start_urls = [
        "https://www.autographfashion.com.au/store/StoreDirectory",
        "https://www.katies.com.au/store/StoreDirectory",
        "https://www.millers.com.au/store/StoreDirectory",
        "https://www.nonib.com.au/store/StoreDirectory",
        "https://www.rivers.com.au/store/StoreDirectory",
        "https://www.rockmans.com.au/store/StoreDirectory",
    ]
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse")]
    brands = {
        "www.autographfashion.com.au": {"brand": "Autograph", "brand_wikidata": "Q120646111"},
        "www.katies.com.au": {"brand": "Katies", "brand_wikidata": "Q120646115"},
        "www.millers.com.au": {"brand": "Millers", "brand_wikidata": "Q120644857"},
        "www.nonib.com.au": {"brand": "Noni B", "brand_wikidata": "Q120645737"},
        "www.rivers.com.au": {"brand": "Rivers", "brand_wikidata": "Q106224813"},
        "www.rockmans.com.au": {"brand": "Rockmans", "brand_wikidata": "Q120646031"},
    }

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
        ldjson = parse_js_object(ldjsontext, json_params={"strict": False})

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
        if properties["state"] == "NZ":
            properties["country"] = "NZ"
            properties.pop("state")
        else:
            properties["country"] = "AU"

        for brand_domain, brand_attributes in self.brands.items():
            if brand_domain in response.url:
                properties.update(brand_attributes)
                break

        hours_text = " ".join(Selector(text=ldjson["openingHours"]).xpath("//text()").getall())
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_text)
        yield Feature(**properties)
