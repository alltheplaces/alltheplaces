from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class VanDalNLSpider(SitemapSpider, StructuredDataSpider):
    name = "van_dal_nl"
    item_attributes = {"brand": "Van Dal", "brand_wikidata": "Q125580449"}
    sitemap_urls = ["https://www.vdal.nl/robots.txt"]
    sitemap_follow = ["branches"]
    sitemap_rules = [(r"winkels/(\d+)/van-dal-[^\.]+\.html$", "parse")]
    wanted_types = ["Store"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Van Dal ")
        item["extras"]["website:nl"] = response.xpath('//link[@rel="alternate"][@hreflang="nl-NL"]/@href').get()
        item["extras"]["website:de"] = response.xpath('//link[@rel="alternate"][@hreflang="de-DE"]/@href').get()
        # item["extras"]["website:nl"] = response.xpath('//link[@rel="alternate"][hreflang="nl-BE"]/@href').get()

        yield item
