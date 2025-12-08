from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

BRANDS = {
    "OfficeMax": {"brand": "OfficeMax", "brand_wikidata": "Q7079111"},
    "Office Depot": {"brand": "Office Depot", "brand_wikidata": "Q1337797"},
}


class OfficeDepotSpider(SitemapSpider, StructuredDataSpider):
    name = "office_depot"
    allowed_domains = ["officedepot.com"]
    sitemap_urls = ["https://www.officedepot.com/storelocator_0.xml"]
    json_parser = "json5"
    requires_proxy = "US"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["website"] = response.url
        if item.get("image") == "http://www.example.com/LocationImageURL":
            item["image"] = None
        if "/office-depot-" in response.url:
            item.update(BRANDS["Office Depot"])
        elif "/officemax-" in response.url:
            item.update(BRANDS["OfficeMax"])
        yield item
