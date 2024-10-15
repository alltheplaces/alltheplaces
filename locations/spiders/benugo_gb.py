from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BenugoGBSpider(SitemapSpider, StructuredDataSpider):
    name = "benugo_gb"
    item_attributes = {"operator": "Benugo", "operator_wikidata": "Q20746208"}
    sitemap_urls = ["https://benugo.com/site-sitemap.xml"]
    drop_attributes = {"twitter", "facebook"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        amenityType = response.url.split("/")[4]
        if amenityType == "cafes":
            item["extras"]["amenity"] = "cafe"
        if amenityType == "restaurants":
            item["extras"]["amenity"] = "restaurant"
        yield item
