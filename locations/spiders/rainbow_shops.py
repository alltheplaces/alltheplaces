import html

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RainbowShopsSpider(SitemapSpider, StructuredDataSpider):
    name = "rainbow_shops"
    allowed_domains = ["stores.rainbowshops.com"]
    item_attributes = {"brand": "Rainbow", "brand_wikidata": "Q7284708"}
    sitemap_urls = ["https://stores.rainbowshops.com/robots.txt"]
    sitemap_rules = [(r"com/\w\w/[^/]+/(\d+)/$", "parse")]
    time_format = "%I:%M%p"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = html.unescape(item.pop("name"))
        item["street_address"] = html.unescape(item["street_address"])
        item["city"] = html.unescape(item["city"])
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()

        if item.get("image") and "wkvygexq0az9oz125oof.jpg" in item["image"]:
            # Ignore logo placeholder images where a specific image of a store
            # does not exist.
            item.pop("image")

        yield item
