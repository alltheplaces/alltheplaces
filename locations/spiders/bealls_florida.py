from re import search
from json import loads
from urllib.parse import unquote
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BeallsFlorida(SitemapSpider, StructuredDataSpider):
    name = "bealls_florida"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    allowed_domains = ["stores.beallsflorida.com"]
    sitemap_urls = ["https://stores.beallsflorida.com/sitemap/sitemap_index.xml"]
    sitemap_rules = [(r"stores\.beallsflorida\.com/fl/\w+/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("image")
        item.pop("facebook")
        item["email"] = unquote(item.pop("email")).strip()

        if m := search(
            r"map_list_data\s*=\s*(.*)", response.xpath('//script[@type="text/javascript"]/text()').extract_first()
        ):
            d = loads(m.group(1))[0]

            item["city"] = d.get("city")
            item["lat"] = d.get("lat")
            item["lon"] = d.get("lng")
            item["name"] = d.get("location_name")
            item["phone"] = d.get("local_phone")
            item["postcode"] = d.get("post_code")
            item["street_address"] = d.get("address_1") + d.get("address_2")

            oh = OpeningHours()
            hours = loads(d.get("hours_sets:primary")).get("days")
            for day in hours.keys():
                oh.add_range(
                    day,
                    hours[day][0]["open"],
                    hours[day][0]["close"],
                )

            item["opening_hours"] = oh.as_opening_hours()

        yield item
