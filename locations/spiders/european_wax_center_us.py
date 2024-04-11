from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EuropeanWaxCenterUSSpider(SitemapSpider, StructuredDataSpider):
    name = "european_wax_center_us"
    item_attributes = {"brand": "European Wax Center", "brand_wikidata": "Q5413426"}
    sitemap_urls = ["https://locations.waxcenter.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/[^/]+-(\d+)\.html$", "parse")]
    wanted_types = ["BeautySalon"]

    def sitemap_filter(self, entries):
        for entry in entries:
            for ignore in [
                "bikini-waxing-",
                "body-waxing-",
                "facial-waxing-",
                "wax-pass-",
                "what-to-expect-",
                "brow-tint-",
            ]:
                if ignore in entry["loc"]:
                    break
            else:
                yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        item["branch"] = response.xpath('//span[@class="location-name"]/text()').get()

        yield item
