import json

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BakersDelightSpider(SitemapSpider, StructuredDataSpider):
    name = "bakers_delight"
    item_attributes = {"brand": "Bakers Delight", "brand_wikidata": "Q4849261"}
    allowed_domains = ["www.bakersdelight.com.au"]
    sitemap_urls = ["https://www.bakersdelight.com.au/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"/bakery-locator/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        data_raw = response.xpath('//script[@id="wpsl-js-js-extra"]/text()').extract_first()
        data_clean = data_raw.split("var wpslMap_0 = ", 1)[1].split(";\n", 1)[0]
        store = json.loads(data_clean)["locations"][0]
        item["ref"] = store["id"]
        item["lat"] = store["lat"]
        item["lon"] = store["lng"]
        if store["country"] == "Australia":
            item["country"] = "AU"
        elif store["country"] == "New Zealand":
            item["country"] = "NZ"
            item.pop("state")
        item.pop("image")
        item.pop("facebook")
        yield item
