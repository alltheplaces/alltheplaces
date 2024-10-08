from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class GrimaldisPizzeriaSpider(SitemapSpider, StructuredDataSpider):
    name = "grimaldis_pizzeria"
    item_attributes = {"brand": "Grimaldi's Pizzeria", "brand_wikidata": "Q564256"}
    allowed_domains = ["www.grimaldispizzeria.com"]
    sitemap_urls = ["https://www.grimaldispizzeria.com/location-sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        for day in response.xpath('//div[@class="info_block hrs"]//tbody//tr'):
            oh.add_range(
                day=day.xpath("./td[1]/text()").get(),
                open_time=day.xpath("./td[2]/text()").get().split(" - ")[0],
                close_time=day.xpath("./td[2]/text()").get().split(" - ")[1],
                time_format="%I:%M %p",
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
