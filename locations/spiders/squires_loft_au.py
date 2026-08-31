import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature

AU_STATE_PATTERN = re.compile(r",?\s*(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)(?:\s+\d{4})?$")


class SquiresLoftAUSpider(SitemapSpider):
    name = "squires_loft_au"
    item_attributes = {"brand": "Squires Loft", "brand_wikidata": "Q141237587"}
    allowed_domains = ["squiresloft.com.au"]
    sitemap_urls = ["https://squiresloft.com.au/our-locations-sitemap.xml"]
    sitemap_rules = [(r"/our-locations/([\w\-]+)/$", "parse")]

    def parse(self, response):
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["addr_full"] = response.xpath('string(//div[@class="cntbox loc_add"]//p)').get("").strip()
        if state := AU_STATE_PATTERN.search(item["addr_full"]):
            item["state"] = state.group(1)
        item["email"] = response.xpath('//div[@class="cntbox lemail_add"]//a/@href').get("").removeprefix("mailto:")
        item["phone"] = response.xpath('//div[@class="cntbox lcon_num"]//a/text()').get()

        branch = response.xpath('//div[@class="stitle"]/h5/text()').get("")
        item["branch"] = branch.removeprefix("SQUIRES LOFT ").title().strip()

        if map_url := response.xpath('//iframe[contains(@data-src, "maps/embed")]/@data-src').get():
            item["lat"], item["lon"] = url_to_coords(map_url)

        oh = OpeningHours()
        for row in response.xpath('//div[@class="timing_offer"]//div[@class="timeslot"]'):
            day = row.xpath("./p/text()").get("").strip().rstrip(":")
            for time_range in row.xpath("./p/span/text()").get("").split("&"):
                oh.add_ranges_from_string(f"{day} {time_range.strip()}")
        item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"

        yield item
