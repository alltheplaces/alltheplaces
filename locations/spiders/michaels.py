import json
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MichaelsSpider(SitemapSpider):
    name = "michaels"
    item_attributes = {"brand": "Michaels", "brand_wikidata": "Q6835667"}
    sitemap_urls = ["https://locations.michaels.com/sitemap.xml.gz", "https://locationsca.michaels.com/sitemap.xml.gz"]
    sitemap_rules = [(r"https://\w+\.michaels\.com/[^/]+/[^/]+/\d+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//*[@id="__NEXT_DATA__" ]/text()').get())["props"]["pageProps"][
            "response"
        ]
        item = DictParser.parse(raw_data)
        item["lat"] = raw_data["coords_latitude"]
        item["lon"] = raw_data["coords_longitude"]
        item["branch"] = raw_data["michaels_store_name"]
        item["website"] = item["ref"] = response.url
        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="css-1h9mp0"]'):
            day = day_time.xpath('.//*[@class="css-87dqa9"]/p/text()').get()
            open_close_time = day_time.xpath("./p/text()").get()
            if open_close_time == "CLOSED":
                oh.set_closed(day)
            else:
                open_time, close_time = open_close_time.split("-")
                oh.add_range(
                    day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                )
        item["opening_hours"] = oh

        yield item

    # api_brand_name = "michaelsca"
    # api_key = "288FB6BC-71EE-11E1-AA2E-C7DA57283E85"
    #
    # def parse_item(self, item, location):
    #     item["state"] = location["state"]
    #     if item["country"] == "US":
    #         item["website"] = (
    #             "https://locations.michaels.com/"
    #             + item["state"].lower()
    #             + "/"
    #             + item["city"].lower().replace(" ", "-")
    #             + "/"
    #             + item["ref"]
    #         )
    #     item["opening_hours"] = OpeningHours()
    #     if location.get("mon_sat") and location.get("mon_sat").upper() != "CLOSED":
    #         item["opening_hours"].add_days_range(
    #             ["Mo", "Tu", "We", "Th", "Fr", "Sa"],
    #             location.get("mon_sat").split(" - ", 1)[0],
    #             location.get("mon_sat").split(" - ", 1)[1],
    #             "%I:%M%p",
    #         )
    #     if location.get("sun") and location.get("sun").upper() != "CLOSED":
    #         item["opening_hours"].add_range(
    #             "Su", location.get("sun").split(" - ", 1)[0], location.get("sun").split(" - ", 1)[1], "%I:%M%p"
    #         )
    #     yield item
