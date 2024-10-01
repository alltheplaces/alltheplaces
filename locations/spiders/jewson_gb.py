import scrapy

from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class JewsonGBSpider(scrapy.spiders.SitemapSpider):
    name = "jewson_gb"
    item_attributes = {"brand": "Jewson", "brand_wikidata": "Q6190226", "country": "GB"}
    sitemap_urls = ["https://www.jewson.co.uk/sitemap/sitemap_branches_jewson.xml"]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "LocalBusiness")
        if item:
            item["ref"] = response.url
            item["lat"] = response.xpath("//@data-latitude").get()
            item["lon"] = response.xpath("//@data-longitude").get()
            yield item
    drop_attributes = {"image"}
