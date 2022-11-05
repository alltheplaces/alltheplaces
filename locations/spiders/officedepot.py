from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.hours import OpeningHours


BRANDS = {
    "OfficeMax": {"brand": "OfficeMax", "brand_wikidata": "Q7079111"},
    "Office Depot": {"brand": "Office Depot", "brand_wikidata": "Q1337797"},
}


class OfficedepotSpider(SitemapSpider, StructuredDataSpider):
    name = "officedepot"
    allowed_domains = ["officedepot.com"]
    sitemap_urls = ["https://www.officedepot.com/storelocator_0.xml"]
    wanted_types = ["LocalBusiness"]
    parse_json_comments = True

    def parse(self, response):
        yield from self.parse_sd(response)

    def inspect_item(self, item, response):
        item["website"] = response.url
        oh = OpeningHours()
        for row in response.css(".thehours .hoursrow"):
            day = row.css(".hourslabel::text").get()
            interval = row.css(".hour::text").get().strip()
            if interval.lower() == "closed":
                continue
            open_time, close_time = interval.split("-")
            oh.add_range(day[:2], open_time, close_time, "%I:%M%p")
        item["opening_hours"] = oh.as_opening_hours()

        name = item["name"] = response.css(".storetitle::text").get().strip()
        item.update(BRANDS[name])

        yield item
