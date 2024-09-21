import json
import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class HomeDepotCASpider(SitemapSpider, StructuredDataSpider):
    name = "home_depot_ca"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["homedepot.ca"]
    sitemap_urls = ["https://stores.homedepot.ca/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.homedepot\.ca\/([\w]{2})\/([-\w]+)\/([-\w]+)([\d]+)\.html$",
            "parse_sd",
        ),
    ]

    def post_process_item(self, item, response, ld_data):
        item["ref"] =  re.search(r".+/.+?([0-9]+).html", response.url).group(1)
        item["branch"] = item.pop("name").replace("The Home Depot: ", "").replace("Home Improvement & Hardware Store in ", ""
        ).replace("Home Depot : Magasin spécialisé en amélioration domiciliaire et en quincaillerie à ", "").replace(".", "")


        hours = self.parse_hours(ld_data.get("openingHours"))
        if hours:
            item["opening_hours"] = hours

        yield item

    # NOTE: This appears to have a higher success rate than the standard one from cursory review, so have left this behaviour
    def parse_hours(self, open_hours):
        opening_hours = OpeningHours()
        location_hours = re.findall(r"([a-zA-Z]*)\s(.*?)\s-\s(.*?)\s", open_hours)

        for weekday in location_hours:
            opening_hours.add_range(day=weekday[0], open_time=weekday[1], close_time=weekday[2])

        return opening_hours.as_opening_hours()
