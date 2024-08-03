from scrapy import FormRequest, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.spiders.ampol_au import AmpolAUSpider
from locations.spiders.bp import BpSpider
from locations.spiders.coles_au import ColesAUSpider
from locations.spiders.exxon_mobil import ExxonMobilSpider
from locations.spiders.liberty_au import LibertyAUSpider
from locations.spiders.night_owl_au import NightOwlAUSpider
from locations.spiders.otr_au import OtrAUSpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES
from locations.spiders.shell import ShellSpider
from locations.spiders.united_petroleum_au import UnitedPetroleumAUSpider


class MoveYourselfAUSpider(Spider):
    name = "move_yourself_au"
    item_attributes = {
        "brand": "Move Yourself",
        "brand_wikidata": "Q126164464",
        "extras": Categories.SHOP_PLANT_HIRE.value,
    }
    allowed_domains = ["www.moveyourself.com.au"]
    start_urls = ["https://www.moveyourself.com.au/index.php"]

    def start_requests(self):
        formdata = {"getmapdata": "true"}
        yield FormRequest(url=self.start_urls[0], formdata=formdata, method="POST", callback=self.parse)

    def parse(self, response):
        for location in response.json()["depos"].values():
            item = DictParser.parse(location)
            item["ref"] = location["depocode"]
            item["name"] = location["deponame"]
            match location["depotype"]:
                case "ampol":
                    item["located_in"] = AmpolAUSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = AmpolAUSpider.item_attributes["brand_wikidata"]
                case "bp":
                    item["located_in"] = BpSpider.brands["bp"]["brand"]
                    item["located_in_wikidata"] = BpSpider.brands["bp"]["brand_wikidata"]
                case "coles":
                    item["located_in"] = ColesAUSpider.BRANDS[1]["brand"]
                    item["located_in_wikidata"] = ColesAUSpider.BRANDS[1]["brand_wikidata"]
                case "liberty":
                    item["located_in"] = LibertyAUSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = LibertyAUSpider.item_attributes["brand_wikidata"]
                case "metro":
                    item["located_in"] = "Metro Petroleum"
                    item["located_in_wikidata"] = "Q111970125"
                case "otr":
                    item["located_in"] = OtrAUSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = OtrAUSpider.item_attributes["brand_wikidata"]
                case "puma":
                    item["located_in"] = "Puma"
                    item["located_in_wikidata"] = "Q7259769"
                case "shell":
                    item["located_in"] = ShellSpider.item_attributes["brand"]
                    item["located_in_wikidata"] = ShellSpider.item_attributes["brand_wikidata"]
                case "united":
                    item["located_in"] = UnitedPetroleumAUSpider.UNITED["brand"]
                    item["located_in_wikidata"] = UnitedPetroleumAUSpider.UNITED["brand_wikidata"]
                case "misc":
                    if item["name"].startswith("7-Eleven "):
                        item["located_in"] = SEVEN_ELEVEN_SHARED_ATTRIBUTES["brand"]
                        item["located_in_wikidata"] = SEVEN_ELEVEN_SHARED_ATTRIBUTES["brand_wikidata"]
                    elif item["name"].startswith("AMPM "):
                        item["located_in"] = "ampm"
                        item["located_in_wikidata"] = "Q306960"
                    elif item["name"].startswith("Atlas Fuels "):
                        item["located_in"] = "Atlas Fuels"
                    elif item["name"].startswith("Boost Fuels "):
                        item["located_in"] = "Boost Fuels"
                    elif item["name"].startswith("Dayef Petroleum "):
                        item["located_in"] = "Dayef Petroleum"
                    elif item["name"].startswith("Mobil "):
                        item["located_in"] = ExxonMobilSpider.brands["Mobil"]["brand"]
                        item["located_in_wikidata"] = ExxonMobilSpider.brands["Mobil"]["brand_wikidata"]
                    elif item["name"].startswith("Night Owl "):
                        item["located_in"] = NightOwlAUSpider.item_attributes["brand"]
                        item["located_in_wikidata"] = NightOwlAUSpider.item_attributes["brand_wikidata"]
                    elif item["name"].startswith("Octane Fuels "):
                        item["located_in"] = "Octane Fuels"
                    elif item["name"].startswith("Pearl Energy "):
                        item["located_in"] = "Pearl Energy"
                    elif item["name"].startswith("Quik Stop "):
                        item["located_in"] = "Quik Stop"
                        item["located_in_wikidata"] = "Q105141709"
                    elif item["name"].startswith("Reddy Express "):
                        item["located_in"] = "Reddy Express"
                    elif item["name"].startswith("S24 "):
                        item["located_in"] = "S24"
                    else:
                        self.logger.warning(
                            "Unknown brand detected for the feature this Move Yourself is located within. Full location name is: {}".format(
                                location["deponame"]
                            )
                        )
                case _:
                    self.logger.warning(
                        "Unknown brand detected for the feature this Move Yourself is located within: {}".format(
                            location["depotype"]
                        )
                    )
            yield item
