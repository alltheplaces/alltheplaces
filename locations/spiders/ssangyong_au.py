from html import unescape
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.ssangyong_kr import SSANGYONG_SHARED_ATTRIBUTES


class SsangyongAUSpider(Spider):
    name = "ssangyong_au"
    item_attributes = SSANGYONG_SHARED_ATTRIBUTES
    allowed_domains = ["kgm.com.au"]
    start_urls = ["https://kgm.com.au/dealers/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for dealer in response.xpath('//div[@id="dealer-columns-section"]/div'):
            properties = {
                "ref": dealer.xpath(".//@dealercode").get(),
                "branch": unescape(dealer.xpath(".//@dealer").get()),
                "lat": dealer.xpath(".//@lat").get(),
                "lon": dealer.xpath(".//@long").get(),
                "addr_full": unescape(dealer.xpath(".//@address").get()),
                "postcode": dealer.xpath(".//@dealerpostcode").get(),
                "state": dealer.xpath(".//@dealerregion").get(),
                "phone": dealer.xpath(".//@phone").get(),
                "email": dealer.xpath(".//@dealeremail").get(),
                "opening_hours": OpeningHours(),
            }
            apply_category(Categories.SHOP_CAR, properties)
            hours_text = "Monday-Friday: {}, Saturday: {}, Sunday: {}".format(
                dealer.xpath(".//@dealeropenmonfri").get(""),
                dealer.xpath(".//@dealeropensaturday").get(""),
                dealer.xpath(".//@dealeropensunday").get(""),
            )
            properties["opening_hours"].add_ranges_from_string(hours_text)
            yield Feature(**properties)
