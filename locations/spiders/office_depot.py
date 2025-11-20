from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OfficeDepotSpider(SitemapSpider, StructuredDataSpider):
    name = "office_depot"
    item_attributes = {"brand": "Office Depot", "brand_wikidata": "Q1337797"}
    allowed_domains = ["officedepot.com"]
    sitemap_urls = ["https://www.officedepot.com/storelocator_0.xml"]
    json_parser = "json5"
    requires_proxy = "US"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        if item.get("image") == "http://www.example.com/LocationImageURL":
            item["image"] = None
        yield item
