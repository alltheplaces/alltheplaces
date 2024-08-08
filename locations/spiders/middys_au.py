from scrapy import Request, Selector, Spider

from locations.hours import OpeningHours
from locations.items import Feature


class MiddysAUSpider(Spider):
    name = "middys_au"
    item_attributes = {"brand": "Middy's", "brand_wikidata": "Q117157352"}
    allowed_domains = ["mybranch.middys.com.au"]
    start_urls = ["https://mybranch.middys.com.au/branch/all"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"Accept": "text/plain; charset=utf-8"},
        "ROBOTSTXT_OBEY": False,
    }

    def start_request(self):
        for url in self.start_urls:
            yield Request(url=url, headers={"X-Requested-With": "XMLHttpRequest"})

    def parse(self, response):
        for location in response.json()["branches"]:
            info_window_html = Selector(text=location["infoWindowHtml"].replace('"', '"').replace("\t", ""))
            properties = {
                "ref": info_window_html.xpath("//h3/a/@href").get().replace("/branch/locator/", ""),
                "name": info_window_html.xpath("//h3/a/text()").get(),
                "lat": location["latitude"],
                "lon": location["longitude"],
                "addr_full": " ".join(
                    info_window_html.xpath("//h3/following::p/text()[position() <= (last() - 2)]").getall()
                ),
                "phone": info_window_html.xpath('(//p/span[contains(@class, "branch-phoneNumber")])[1]/text()').get(),
                "email": info_window_html.xpath(
                    '//span[contains(@class, "branch-phoneNumber")]/a[contains(@href, "mailto:")]/@href'
                )
                .get()
                .replace("mailto:", ""),
                "website": "https://mybranch.middys.com.au" + info_window_html.xpath("//h3/a/@href").get(),
            }
            properties["image"] = "https://mybranch.middys.com.au/images/branch/" + properties["ref"] + ".jpg"

            properties["opening_hours"] = OpeningHours()
            hours_string = " ".join(
                (" ".join(info_window_html.xpath('//div[contains(@class, "branchTimings")]//text()').getall())).split()
            )
            day_pairs = [
                ["Monday", "Tuesday"],
                ["Tuesday", "Wednesday"],
                ["Wednesday", "Thursday"],
                ["Thursday", "Friday"],
                ["Friday", "Saturday"],
                ["Saturday", "Sunday"],
                ["Sunday", "Monday"],
            ]
            for day_pair in day_pairs:
                if day_pair[0] not in hours_string and day_pair[1] not in hours_string:
                    hours_string = hours_string.replace("Today", day_pair[0]).replace("Tomorrow", day_pair[1])
                    break
            properties["opening_hours"].add_ranges_from_string(hours_string)

            yield Feature(**properties)
