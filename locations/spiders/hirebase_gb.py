from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class HirebaseGBSpider(SitemapSpider, StructuredDataSpider):
    name = "hirebase_gb"
    item_attributes = {
        "brand": "Hirebase",
        "brand_wikidata": "Q100297859",
    }

    # "DefaultLat":"54.072815","DefaultLng":"-4.421120"
    sitemap_urls = ["https://www.hirebase.uk/robots.txt"]
    sitemap_rules = [
        (r"https://www.hirebase.uk/storefinder/store/[\w-]+-\d+", "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        """Override with any post-processing on the item."""
        js_blob = response.xpath("//script[contains(text(),'DefaultLat')]/text()").get()
        if js_blob:
            item["lat"] = js_blob.split('DefaultLat":"')[1].split('","')[0]
            item["lon"] = js_blob.split('DefaultLng":"')[1].split('","')[0]

        yield item
