import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BobJaneTmartsAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bob_jane_tmarts_au"
    item_attributes = {"brand_wikidata": "Q16952468"}
    allowed_domains = ["www.bobjane.com.au"]
    sitemap_urls = ["https://www.bobjane.com.au/sitemaps/public/store_search.xml.gz"]
    sitemap_rules = [
        (r"shop/.*$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"], item["lon"] = self.parse_lat_lon(response)
        yield from self.inspect_item(item, response)

    @staticmethod
    def parse_lat_lon(response):
        # Raw text is: location&quot;:&quot;-37.99739838,145.22099304&quot
        props = response.xpath('//div[@data-react-class="ShopHeader"]/@data-react-props').get().replace("&quot;", '"')
        match = re.search(r'"location":"([\-\d\.]+),([\d\.]+)"', props)
        if match:
            return (float(match.group(1)), float(match.group(2)))
        else:
            return (None, None)
