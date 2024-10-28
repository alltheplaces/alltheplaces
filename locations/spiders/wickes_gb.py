import html

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WickesGBSpider(SitemapSpider, StructuredDataSpider):
    name = "wickes_gb"
    item_attributes = {"brand": "Wickes", "brand_wikidata": "Q7998350"}
    sitemap_urls = ["https://www.wickes.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.wickes\.co\.uk\/store\/(\d+)$", "parse_sd")]
    drop_attributes = {"image"}
    wanted_types = ["Place"]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = html.unescape(item.pop("name")).removeprefix("Wickes ")

        item["lat"] = response.xpath("//@data-latitude").get()
        item["lon"] = response.xpath("//@data-longitude").get()
        yield item
