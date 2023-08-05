from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FedExSpider(SitemapSpider, StructuredDataSpider):
    name = "fedex"
    item_attributes = {"brand": "FedEx", "brand_wikidata": "Q459477"}
    sitemap_urls = [
        "https://local.fedex.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"\/[a-z0-9]{4,5}$", "parse_sd"),
        (r"\/office-[0-9]{4}$", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["email"] = response.xpath('//a[@class="Hero-emailLink Link--primary"]/@href').extract_first()
        if item["email"]:
            item["email"] = item["email"][5:]

        item["city"] = response.xpath('//span[@class="Address-field Address-city"]/text()').extract_first()

        yield item
