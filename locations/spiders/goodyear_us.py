from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoodyearUSSpider(SitemapSpider, StructuredDataSpider):
    name = "goodyear_us"
    item_attributes = {"brand": "Goodyear", "brand_wikidata": "Q620875"}
    sitemap_urls = ["https://www.goodyearautoservice.com/sitemap-retail-locations-sitemap-GAS.xml"]
    sitemap_rules = [("/location/", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["lat"] = ld_data.get("areaServed", {}).get("geoMidpoint", {}).get("latitude")
        item["lon"] = ld_data.get("areaServed", {}).get("geoMidpoint", {}).get("longitude")

        yield item
