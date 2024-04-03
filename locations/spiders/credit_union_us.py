from geonamescache import GeonamesCache
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours


class CreditUnionUSSpider(CSVFeedSpider):
    name = "credit_union_us"
    item_attributes = {"extras": Categories.BANK.value}
    allowed_domains = ["co-opcreditunions.org"]
    no_refs = True

    def start_requests(self):
        for state in GeonamesCache().get_us_states().keys():
            yield Request(
                url="https://co-opcreditunions.org/wp-content/themes/coop019901/inc/locator/locator-csv.php?loctype=S&state={}&statewide=yes&country=&Submit=Search&lp=1%22".format(
                    state
                )
            )

    def parse_row(self, response: Response, row: dict):
        item = DictParser.parse(row)
        item["country"] = item["country"].strip()
        item["street_address"] = item.pop("addr_full")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_3_LETTERS:
            open_time = row.get("Hours{}Open".format(day))
            close_time = row.get("Hours{}Close".format(day))
            if open_time and open_time != "Closed":
                item["opening_hours"].add_range(day, open_time, close_time)

        yield item
