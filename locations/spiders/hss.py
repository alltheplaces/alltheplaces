from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HssSpider(SitemapSpider, StructuredDataSpider):
    name = "hss"
    item_attributes = {
        "brand": "HSS Hire",
        "brand_wikidata": "Q5636000",
    }
    sitemap_urls = ["https://www.hss.com/robots.txt"]
    sitemap_rules = [
        (r"https://www.hss.com/hire/find-a-branch/[\w-]+/[\w-]+", "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs): 
        """Override with any post-processing on the item."""
        js_blob = response.xpath("//div[@class='google_map']/script/text()").get()
        if js_blob:
            item['lat'] = js_blob.split("latitude = ")[1].split(";")[0]
            item['lon'] = js_blob.split("longitude = ")[1].split(";")[0]

        yield item
