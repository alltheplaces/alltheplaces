from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class TheNottinghamGBSpider(SitemapSpider, StructuredDataSpider):
    name = "the_nottingham_gb"
    item_attributes = {"brand": "The Nottingham", "brand_wikidata": "Q7063598"}
    sitemap_urls = ["https://www.thenottingham.com/sitemap.xml"]
    sitemap_rules = [(r"/branches/[\w-]+$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = float(response.xpath("//@data-lat").get())
        item["lon"] = float(response.xpath("//@data-lng").get())
        item["addr_full"] = response.xpath('//li[@class="location"]/text()').get()
        item["branch"] = item.pop("name", "").removeprefix("The Nottingham - ").removesuffix(" Branch")
        item["ref"] = response.url.split("/branches/")[-1]

        oh = OpeningHours()
        oh.add_ranges_from_string(" ".join(response.xpath('//div[@class="hours"]//text()').getall()))
        item["opening_hours"] = oh

        apply_category(Categories.BANK, item)
        yield item
