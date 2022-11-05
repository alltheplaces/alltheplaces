from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GapSpider(SitemapSpider, StructuredDataSpider):
    name = "gap"
    item_attributes = {"brand": "Gap", "brand_wikidata": "Q420822", "country": "US"}
    allowed_domains = ["www.gap.com"]
    sitemap_urls = ["https://www.gap.com/stores/sitemap.xml"]
    sitemap_rules = [
        (r"https:\/\/www\.gap\.com\/stores\/\w{2}\/\w+\/gap-(\d+)\.html$", "parse_sd")
    ]
    wanted_types = ["ClothingStore"]

    def inspect_item(self, item, response):
        item["name"] = response.xpath(
            'normalize-space(//div[@class="location-name"]/text())'
        ).get()

        item["brand"] = (
            response.xpath('normalize-space(//div[@class="store-carries"]/text())')
            .get()
            .replace(", ", "; ")
        )

        item["image"] = None

        yield item
