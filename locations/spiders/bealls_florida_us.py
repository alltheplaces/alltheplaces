from json import loads
from re import search
from urllib.parse import unquote

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BeallsFloridaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bealls_florida_us"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    allowed_domains = ["stores.beallsflorida.com"]
    sitemap_urls = ["https://stores.beallsflorida.com/sitemap/sitemap_index.xml"]
    sitemap_rules = [(r"stores\.beallsflorida\.com/fl/\w+/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        email = unquote(item.pop("email")).strip()
        ref = item.pop("ref")

        if m := search(
            r"map_list_data\s*=\s*(.*)", response.xpath('//script[@type="text/javascript"]/text()').extract_first()
        ):
            d = loads(m.group(1))[0]

            item = DictParser.parse(d)
            item.pop("street")
            item.pop("housenumber")
            item["name"] = d.get("location_name")
            item["phone"] = d.get("local_phone")
            item["street_address"] = d.get("address_1") + d.get("address_2")
            item["opening_hours"] = OpeningHours()

            hours = loads(d.get("hours_sets:primary")).get("days")
            for day in hours.keys():
                item["opening_hours"].add_range(
                    day,
                    hours[day][0]["open"],
                    hours[day][0]["close"],
                )
        item["email"] = email
        item["ref"] = ref

        yield item
