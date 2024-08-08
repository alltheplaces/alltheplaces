from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class IcelandFoodsSpider(SitemapSpider, StructuredDataSpider):
    name = "iceland_foods"
    item_attributes = {"brand": "Iceland", "brand_wikidata": "Q721810"}
    allowed_domains = ["www.iceland.co.uk"]
    sitemap_urls = ["https://www.iceland.co.uk/sitemap-store-site-map.xml"]
    sitemap_rules = [
        (
            r"https://www\.iceland\.co\.uk/store-finder/store\?StoreID=(\d+)&StoreName=",
            "parse_sd",
        )
    ]
    wanted_types = ["LocalBusiness"]
    search_for_phone = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["extras"]["branch"] = response.xpath("/html/head/title/text()").get()
        item["name"] = None

        if "FWH" in item["extras"]["branch"] or "Food Ware" in item["extras"]["branch"]:
            # The Food Warehouse, obtained via its own spider
            # The name usually ends with FWH or has Food Warehouse, sometime truncated.
            return

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath("//store-hours/div"):
            day = rule.xpath("./text()").get()
            times = rule.xpath('.//div[@class="store-opening-hours"]/text()').getall()
            if times == ["Closed"]:
                continue
            item["opening_hours"].add_range(day, times[0].strip(), times[1].strip(), time_format="%I:%M%p")

        if item["opening_hours"].as_opening_hours() == "24/7":
            # Closed stores, but with the website left up :(
            # eg https://www.iceland.co.uk/store-finder/store?StoreID=88&StoreName=BATH%20HAM%20GDNS
            return

        if "IRELAND" in item["extras"]["branch"]:
            item["country"] = "IE"
        else:
            item["country"] = "GB"

        if phone := response.xpath('//div[@class="phone"]/text()').get():
            item["phone"] = phone.strip()

        yield item
