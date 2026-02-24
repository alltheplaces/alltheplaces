from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GoApeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "go_ape_gb"
    item_attributes = {"brand": "Go Ape", "brand_wikidata": "Q5574692"}
    sitemap_urls = ["https://goape.co.uk/sitemap-index.xml"]
    sitemap_rules = [(r"https:\/\/goape\.co\.uk\/locations\/([-\w]+)/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = item.pop("street_address").removeprefix("Go Ape ")
        item["branch"] = item.pop("name").removeprefix("Go Ape ")
        item["ref"] = response.url
        yield item
