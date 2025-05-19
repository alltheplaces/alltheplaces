from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BlankStreetCoffeeSpider(SitemapSpider, StructuredDataSpider):
    name = "blank_street_coffee"
    item_attributes = {"brand": "Blank Street Coffee", "brand_wikidata": "Q114792509"}
    sitemap_urls = ["https://www.blankstreet.com/sitemap.xml"]
    sitemap_rules = [(r"com/locations/", "parse_sd")]
    wanted_types = ["CafeOrCoffeeShop"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Extract reference ID from URL
        # URL format: /locations/city/ID-location-name
        url_parts = response.url.split("/")
        if len(url_parts) > 5:
            ref = url_parts[5].split("-")[0]
            item["ref"] = ref

        # Extract branch from the name if it has address info
        if item.get("name") and " at " in item["name"]:
            parts = item["name"].split(" at ")
            item["name"] = parts[0]
            item["branch"] = parts[1]

        yield item
