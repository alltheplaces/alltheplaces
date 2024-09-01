import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import PaymentMethods, map_payment
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

SPUR_COUNTRIES = [
    "au",
    "bw",
    "ke",
    "mu",
    "na",
    "ng",
    "sz",
    "za",
    "zm",
    "zw",
]


class SpurSpider(CrawlSpider):
    name = "spur"
    item_attributes = {"brand": "Spur", "brand_wikidata": "Q7581546"}
    start_urls = [f"https://www.spursteakranches.com/{cc}/find-a-spur" for cc in SPUR_COUNTRIES]
    base_url = "https://www.spursteakranches.com"
    allowed_domains = ["spursteakranches.com"]
    rules = [Rule(LinkExtractor(allow=r"spursteakranches.com/\w\w/restaurant/[\/\-\w()]+$"), callback="parse")]
    no_refs = True

    def process_results(self, response, results):
        # Doing this rather than sitemap because the sitemap only had ZA locations, not other countries
        yield from results
        if (next_url := response.xpath('.//a[@class="paginator-next active"]/@href').get()) is not None:
            yield response.follow(self.base_url + next_url)

    def parse(self, response):
        app_json = json.loads(
            response.xpath('normalize-space(//script[@type="application/ld+json"]/text())').extract_first()
        )
        location = app_json["mainEntity"]

        item = DictParser.parse(location)
        item["city"] = location["address"].get("addressLocality")
        item["state"] = location["address"].get("addressRegion")
        if item["state"] == "International":
            item.pop("state")
        item["country"] = location["address"]["addressCountry"]
        item["postcode"] = location["address"].get("postalCode")

        payments = location["paymentAccepted"][0].split(", ")
        for payment in payments:
            if not map_payment(item, payment, PaymentMethods):
                self.crawler.stats.inc_value(f"atp/{self.name}/payment/fail/{payment}")

        item["opening_hours"] = OpeningHours()
        if location.get("openingHours") is not None:
            item["opening_hours"].add_ranges_from_string(location.get("openingHours")),

        yield item
