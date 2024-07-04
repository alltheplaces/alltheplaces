import scrapy

from locations.linked_data_parser import LinkedDataParser


class TapiGBSpider(scrapy.spiders.SitemapSpider):
    name = "tapi_gb"
    item_attributes = {
        "brand": "Tapi",
        "brand_wikidata": "Q79223951",
    }
    allowed_domains = ["tapi.co.uk"]
    sitemap_urls = ["https://www.tapi.co.uk/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_store")]

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "HomeGoodsStore")
        if item:
            item["ref"] = response.url
            if item.get("image") != "https://www.tapi.co.uk/":  # drop fake SEO "locations" pretending to be shops
                yield item
