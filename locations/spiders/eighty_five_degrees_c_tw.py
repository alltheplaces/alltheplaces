import re
from urllib.parse import parse_qs, urlparse

from scrapy import Spider
from scrapy.http import FormRequest

from locations.google_url import extract_google_position
from locations.hours import DAYS_CN, OpeningHours
from locations.items import Feature

DELIMITERS_CN = ["~", "-", "至"]
NAMED_TIMES_CN = {"24小時": ["00:00", "23:59"]}

days_hours_re_1 = re.compile(r"([~、一-三二-定日星期-週]{2,})\s*：?\s*([0-9:~上小早時晚-]{2,})")
days_hours_re_2 = re.compile(r"([0-9:~上小早時晚-]{2,})\(([~、一-三二-定日星期-週]{2,})\)")


class EightyFiveDegreesCTWSpider(Spider):
    name = "eighty_five_degrees_c_tw"
    item_attributes = {"brand": "85度C", "brand_wikidata": "Q4644852"}
    start_urls = ["https://www.85cafe.com/stores.php"]

    def parse(self, response):
        for city in response.xpath("//div[@class='SR_city']/text()").getall():
            yield FormRequest(
                "https://www.85cafe.com/storeslist.php",
                formdata={"storearea": "選擇區域", "storecity": city},
                callback=self.parse_city,
            )

    def parse_city(self, response):
        for loc in response.xpath("//a[starts-with(@href, 'storein.php')]/@href").getall():
            yield response.follow(loc, callback=self.parse_location)

    def parse_location(self, response):
        item = Feature()
        item["website"] = response.url
        item["ref"] = parse_qs(urlparse(response.url).query)["data"][0]
        item["branch"] = response.xpath("//div[@class='Store_INtitle']/text()").get()
        extract_google_position(item, response)
        item["phone"] = response.xpath("//td[text()='電話']/following-sibling::td[1]/text()").get()
        item["addr_full"] = response.xpath("//td[text()='位址']/following-sibling::td[1]/text()").get()

        fax = response.xpath("//td[text()='傳真']/following-sibling::td[1]/text()").get()
        if fax != "無":
            item["extras"]["fax"] = fax

        business_hours = response.xpath("//td[text()='營業時間']/following-sibling::td[1]/text()").get()
        oh = OpeningHours()
        if any(day in business_hours for day in DAYS_CN):
            for days, hours in days_hours_re_1.findall(business_hours) or map(
                reversed, days_hours_re_2.findall(business_hours)
            ):
                hours = hours.replace("早上", "").replace("晚上", "")
                for days_range in days.split("、"):
                    try:
                        oh.add_ranges_from_string(
                            f"{days_range} {hours}", days=DAYS_CN, named_times=NAMED_TIMES_CN, delimiters=DELIMITERS_CN
                        )
                    except ValueError as e:
                        self.logger.exception(e)
                        oh = None
                        break
                if oh is None:
                    break
        else:
            oh.add_ranges_from_string(f"Daily {business_hours}", named_times=NAMED_TIMES_CN, delimiters=DELIMITERS_CN)
        if oh is not None:
            item["opening_hours"] = oh

        yield item
