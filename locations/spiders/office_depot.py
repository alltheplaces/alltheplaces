from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

BRANDS = {
    "OfficeMax": {"brand": "OfficeMax", "brand_wikidata": "Q7079111"},
    "Office Depot": {"brand": "Office Depot", "brand_wikidata": "Q1337797"},
}


class OfficeDepotSpider(SitemapSpider, StructuredDataSpider):
    name = "office_depot"
    allowed_domains = ["officedepot.com"]
    sitemap_urls = ["https://www.officedepot.com/storelocator_0.xml"]
    json_parser = "json5"
    requires_proxy = "US"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        if item.get("image") == "http://www.example.com/LocationImageURL":
            item["image"] = None
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
