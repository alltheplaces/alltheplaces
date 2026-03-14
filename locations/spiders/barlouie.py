import json

from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class BarlouieSpider(SitemapSpider):
    name = "barlouie"
    allowed_domains = ["www.barlouie.com"]
    item_attributes = {"brand": "Bar Louie", "brand_wikidata": "Q16935493"}
    sitemap_urls = ["https://www.barlouie.com/sitemap.xml"]
    sitemap_rules = [("/locations/", "parse")]

    def parse(self, response):
        for ldjson in response.xpath(
            "//script[@type='application/ld+json' and contains(text(), 'Restaurant')]/text()"
        ).extract():
            try:
                data = json.loads(ldjson)
            except:
                sanitized_data = self.sanitize_json(ldjson)
                data = json.loads(sanitized_data)
            item = LinkedDataParser.parse_ld(data)
            item["ref"] = item["website"] = response.url
            item["image"] = item.get("image", "").replace(
                "https://www.barlouie.comhttps://images.prismic.io",
                "https://images.prismic.io",
            )
            yield item

    def sanitize_json(self, data):
        start_index = data.find('"TimeZoneOffsetSeconds"')
        end_index = data.find("]", start_index)
        return data[: start_index - 7] + data[end_index - 1 :]
