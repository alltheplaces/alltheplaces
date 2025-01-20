import re
from urllib.parse import urljoin, urlparse

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class TexasRoadhouseSpider(scrapy.Spider):
    name = "texas_roadhouse"
    item_attributes = {
        "brand": "Texas Roadhouse",
        "brand_wikidata": "Q7707945",
    }
    allowed_domains = ["www.texasroadhouse.com"]
    start_urls = ("https://www.texasroadhouse.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        location_urls = response.xpath("//url/loc/text()").getall()
        for path in location_urls:
            url = urlparse(path)
            m = re.match(r"/locations/([-\w]+)", url.path)
            if m:
                # IDs starting with "null" are probably closed or future locations
                if m.group(1).startswith("null"):
                    continue
                # Change domain from incorrect http://live-texas-roadhouse-marketing.pantheonsite.io
                url = url._replace(scheme="https", netloc="www.texasroadhouse.com")
                yield scrapy.Request(
                    url.geturl(),
                    callback=self.parse_location,
                )

    def parse_location(self, response):
        item = Feature()

        branch = response.css(".vendor-block-content-top h2::text").get().strip()
        # Reject future locations
        if "(Opening" in branch:
            return
        item["branch"] = branch
        item["ref"] = response.url.split("/")[-1]
        item["addr_full"] = merge_address_lines(response.css(".store-address::text").getall())
        item["website"] = response.url
        item["facebook"] = response.css(".store-facebookurl a::attr(href)").get().strip()

        oh = OpeningHours()
        for line in response.css(".open-dine-hours ul li").getall():
            oh.add_ranges_from_string(line)
        item["opening_hours"] = oh.as_opening_hours()

        item["extras"]["website:orders"] = urljoin(
            response.url, response.css(".cta-ordering a[href$='/start-order']::attr(href)").get()
        )
        item["extras"]["website:menu"] = urljoin(
            response.url, response.css(".cta-ordering a[href$='/digital-menu']::attr(href)").get()
        )

        yield item
