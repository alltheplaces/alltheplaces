from scrapy import Request, Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.react_server_components import parse_rsc


class LAndLHawaiianBarbecueUSSpider(Spider):
    name = "l_and_l_hawaiian_barbecue_us"
    item_attributes = {
        "brand": "L&L Hawaiian Barbecue",
        "brand_wikidata": "Q6455441",
    }

    async def start(self):
        yield Request("https://www.hawaiianbarbecue.com/locations", headers={"rsc": "1"})

    def parse(self, response):
        for location in DictParser.get_nested_key(dict(parse_rsc(response.body)), "locations"):
            item = DictParser.parse(location)
            item["ref"] = location["uid"]
            item["website"] = response.urljoin(location["href"])
            item["branch"] = item.pop("name")

            apply_category(Categories.FAST_FOOD, item)
            apply_yes_no(Extras.TAKEAWAY, item, True)
            item["extras"]["cuisine"] = "hawaiian"

            yield item
