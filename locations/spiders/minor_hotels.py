import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MinorHotelsSpider(SitemapSpider, StructuredDataSpider):
    name = "minor_hotels"
    item_attributes = {"operator": "Minor Hotels", "operator_wikidata": "Q25108728"}
    sitemap_urls = ["https://www.minorhotels.com/en/sitemap_minor_en.xml"]
    sitemap_rules = [(r"/en/destinations/[-\w]+/[-\w]+/[-\w]+$", "parse_sd")]
    BRANDS = {
        "AN": ("Anantara", "Q112671781"),
        "AV": ("Avani Hotels & Resorts", "Q48989823"),
        "EW": ("Elewana", None),
        "NC": ("NH Collection Hotels", "Q1604631"),
        "NH": ("NH Hotels", "Q1604631"),
        "NW": ("nhow", "Q1604631"),
        "OH": ("Oaks Hotels, Resorts & Suites", "Q23073772"),
        "TI": ("Tivoli Hotels & Resorts", "Q10382766"),
    }

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        location_info = chompjs.parse_js_object(response.xpath('//script[contains(text(),"brandcode")]/text()').get())
        item["ref"] = location_info.get("hotelcode")
        item["brand"], item["brand_wikidata"] = self.BRANDS.get(
            location_info.get("brandcode"), (location_info.get("brandname"), None)
        )
        apply_category(Categories.HOTEL, item)
        yield item
