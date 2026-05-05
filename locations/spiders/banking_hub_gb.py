import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class BankingHubGBSpider(CrawlSpider):
    name = "banking_hub_gb"
    item_attributes = {
        "brand": "Banking Hub",
        "brand_wikidata": "Q131824197",
        "operator_wikidata": "Q1783168",
    }
    start_urls = ["https://www.cashaccess.co.uk/hubs/"]
    allowed_domains = ["cashaccess.co.uk"]
    rules = [Rule(LinkExtractor(allow=r"\/hubs\/[-a-z]+\/$"), callback="parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()

        for label in response.xpath("//*[@class='banking-hub-details__label']/text()").getall():
            if re.search("expected", label.lower()):
                # remove "coming soon" branches from results
                return

        item["ref"] = response.url.removeprefix("https://www.cashaccess.co.uk/hubs/").removesuffix("/")
        item["name"] = re.sub(r" \([^\)]+\)$", "", response.xpath("//meta[@property='og:title']/@content").get())
        item["addr_full"] = merge_address_lines(
            response.xpath("//div[@class='banking-hub-details__address']/a//text()").getall()
        )

        item["website"] = response.url

        oh = OpeningHours()

        for a in response.xpath("//*[@class='banking-hub-details__opening-hours-list-item']"):
            day = a.xpath(".//*[@class='banking-hub-details__label']/text()").get()
            hours = a.xpath(".//*[@class='banking-hub-details__opening-hours-daily-list-item']/text()").get()
            if day and hours:
                oh.add_ranges_from_string(day + hours)

        if oh:
            item["opening_hours"] = oh
        else:
            # Drop 'branches' without opening hours, in particular https://www.cashaccess.co.uk/hubs/community-banker-services/
            return

        return item
