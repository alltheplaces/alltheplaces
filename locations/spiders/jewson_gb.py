import scrapy

from locations.structured_data_spider import StructuredDataSpider


class JewsonGBSpider(scrapy.spiders.SitemapSpider, StructuredDataSpider):
    name = "jewson_gb"
    item_attributes = {"brand": "Jewson", "brand_wikidata": "Q6190226", "country": "GB"}
    sitemap_urls = ["https://www.jewson.co.uk/sitemap/sitemap_branches_jewson.xml"]
    download_delay = 0.5
    drop_attributes = {"image", "name"}
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data):
        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        yield item
