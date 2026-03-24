import xmltodict
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ChurchOfScotlandGBSpider(Spider):
    name = "church_of_scotland_gb"
    item_attributes = {"operator": "Church of Scotland", "operator_wikidata": "Q922480"}
    start_urls = [
        "https://cos.churchofscotland.org.uk/church-finder/phpsqlsearch_genxml?latitude=56.1&longitude=-3.9&radius=1000&limit=2000"
    ]

    def parse(self, response, **kwargs):
        data = xmltodict.parse(response.text, attr_prefix="")
        for church in data["churches"]["church"]:
            item = DictParser.parse(church)
            item["name"] = church["church_name"]
            apply_category(Categories.PLACE_OF_WORSHIP, item)
            item["extras"]["religion"] = "christian"
            item["extras"]["denomination"] = "presbyterian"
            yield item
