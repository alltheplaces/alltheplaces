from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BrooksBrothersUSSpider(SitemapSpider, StructuredDataSpider):
    name = "brooks_brothers_us"
    item_attributes = {
        "brand": "Brooks Brothers",
        "brand_wikidata": "Q929722",
    }
    sitemap_urls = ["https://stores.brooksbrothers.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://stores.brooksbrothers.com/\w+/[\w-]+/[\w-]+", "parse"),
    ]
    search_for_facebook = False
    search_for_twitter = False
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("Brooks Brothers ")
        yield item
