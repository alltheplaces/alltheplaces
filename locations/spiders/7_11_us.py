import scrapy
import json

from locations.dict_parser import DictParser


class SevenElevenUSSpider(scrapy.spiders.SitemapSpider):
    name = "seven_eleven_us"
    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}
    allowed_domains = ["7-eleven.com"]
    sitemap_urls = ["https://www.7-eleven.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]
    download_delay = 1.0

    def parse(self, response):
        for ld in response.xpath('//script[@type="application/json"]//text()').getall():
            ld_obj = json.loads(ld, strict=False)
            store = DictParser.get_nested_key(ld_obj, "locations")
            if not store:
                continue
            current_store = DictParser.get_nested_key(store, "currentStore")
            current_store["location"] = store["localStoreLatLon"]
            current_store["street_address"] = current_store["address"]
            del current_store["address"]
            item = DictParser.parse(current_store)
            item["website"] = item["ref"] = response.url
            yield item
