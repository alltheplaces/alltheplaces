import json
import re

import scrapy

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class MarinerFinanceSpider(scrapy.Spider):
    name = "mariner_finance"
    item_attributes = {"brand": "Mariner Finance"}
    allowed_domains = ["www.marinerfinance.com", "loans.marinerfinance.com"]
    start_urls = [
        "https://www.marinerfinance.com/location-sitemap.xml",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//loc[not (contains(text(), '.jpg'))]/text()").getall()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        branch = response.xpath('//h2[contains(text(), "Address")]/following::a/following::text()').extract_first()
        branch_number = re.search(r"Branch Number:\s([0-9]+)\s*.*", branch).group(1)

        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )

        meta = {
            "name": data["name"],
            "ref": branch_number,
            "addr_full": data["address"]["streetAddress"].strip(),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": "US",
            "phone": data.get("telephone"),
            "website": data.get("url") or response.url,
        }
        zipcode = meta["postcode"]

        headers = {
            "Connection": "keep-alive",
            "sec-ch-ua": '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
            "sec-ch-ua-mobile": "?0",
            "User-Agent": BROWSER_DEFAULT,
            "sec-ch-ua-platform": '"Linux"',
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://loans.marinerfinance.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://loans.marinerfinance.com/branchlocatorpage",
            "Accept-Language": "en-US,en;q=0.9",
        }

        yield scrapy.Request(
            url="https://loans.marinerfinance.com/getResults",
            method="POST",
            body=json.dumps({"zipcode": f"{zipcode}"}),
            headers=headers,
            meta=meta,
            callback=self.parse_branch_locator,
        )

    def parse_branch_locator(self, response):
        properties = response.meta
        [properties.pop(k) for k in ["download_timeout", "download_slot", "download_latency", "depth"]]  # pop meta keys
        branch_results = json.loads(response.text)
        branch_data = branch_results["branchData"]
        branch_number = properties.get("ref")

        lat, lon = ("", "")
        for branch in branch_data:
            if branch["BranchNumber"] == branch_number:
                lat = branch.get("latitude")
                lon = branch.get("longitude")

        properties["lat"] = lat
        properties["lon"] = lon

        yield Feature(**properties)
