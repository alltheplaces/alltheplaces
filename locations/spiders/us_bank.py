import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class UsBankSpider(SitemapSpider):
    name = "us_bank"
    download_delay = 0.5
    concurrent_requests = 3
    item_attributes = {"brand": "U.S. Bank", "brand_wikidata": "Q739084"}
    allowed_domains = ["usbank.com"]
    sitemap_urls = [
        "https://www.usbank.com/locations/sitemap.xml",
    ]
    sitemap_rules = [("/locations/([a-z-]*)/([.a-z-]*)/([.0-9a-z-]*)/", "parse_store_info")]

    def opening_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["dayOfTheWeek"]
            start = hour.get("openingTime")
            end = hour.get("closingTime")

            opening_hours.add_range(day=day, open_time=start, close_time=end, time_format="%H:%M:%S")

        return opening_hours.as_opening_hours()

    def parse_store_info(self, response):
        data = json.loads(response.xpath('//script[@type="application/json"]/text()').extract_first())

        branch_data = data["props"]["pageProps"]["branchData"]
        item = DictParser.parse(branch_data)
        apply_category(Categories.BANK, item)
        item["website"] = response.url
        del item["name"]

        branch_detail = branch_data["branchDetail"]
        item["branch"] = branch_detail.get("nickName")
        item["phone"] = branch_detail.get("phoneNumber")
        item["opening_hours"] = self.opening_hours(branch_detail.get("branchHours", []))
        item["ref"] = branch_detail.get("branchNumber")
        item["located_in"] = branch_detail.get("inStoreNm")
        item["extras"]["fax"] = branch_detail.get("faxNumber")

        imagesData = data["props"]["pageProps"].get("branchImagesData")
        if imagesData is not None:
            images = imagesData.get("entities", [])
            if len(images) > 0:
                links = images[0].get("links", [])
                if len(links) > 0:
                    item["image"] = links[0].get("href")
                    if item["image"].endswith(".json"):
                        item["image"] = item["image"][:-5]

        apply_yes_no(
            Extras.ATM, item, branch_detail.get("numberOfWalkUpATMs", 0) + branch_detail.get("numberOfDriveUpATMs", 0)
        )
        apply_yes_no(Extras.DRIVE_THROUGH, item, branch_detail.get("numberOfDriveUpATMs", 0))

        yield item
