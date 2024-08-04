import os
import pathlib

from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

LABELS = [
    # EN
    "locations",
    "stores",
    "find a store",
    # FR
    "magazin",
    # DE
    "mein markt",
    # ES
    "tiendas",
    # Stores
    "botigues",
    "butiker",
    "butikker",
    "búðir",
    "cửa hàng",
    "dendak",
    "do'konlar",
    "dyqane",
    "faleoloa",
    "historias",
    "I negozi",
    "kauplustes",
    "kedai-kedai",
    "lojas",
    "maduka",
    "magasins",
    "magazine",
    "mağazalar",
    "myymälöissä",
    "ngaahi falekoloa",
    "obchodoch",
    "obchody",
    "parduotuvėse",
    "shops",
    "siopau",
    "siopaí",
    "sklepy",
    "stores",
    "toa",
    "toko",
    "trgovine",
    "veikalos",
    "winkels",
    "üzletek",
    "ħwienet",
    "προμήθεια",
    "дэлгүүрүүд",
    "кибетләр",
    "магазинах",
    "магазини",
    "магазины",
    "продавницама",
    "продавници",
    "խանութներ",
    # Locations
    "asukohad",
    "emplacements",
    "helyszíneken",
    "joylar",
    "kokapenak",
    "liggings",
    "lleoliadau",
    "Localizações",
    "locaties",
    "locații",
    "locis",
    "lokacije",
    "lokalizacje",
    "lokasi",
    "láithreacha",
    "maeneo",
    "miest",
    "nga waahi",
    "ngaahi feitu'u",
    "nofoaga",
    "panggonan",
    "placeringer",
    "platser",
    "posizioni",
    "postijiet",
    "sijainnit",
    "standorte",
    "staðsetningar",
    "steder",
    "ubicaciones",
    "ubicacions",
    "umístění",
    "vendndodhjet",
    "vietas",
    "vietos",
    "yerler",
    "địa điểm",
    "τοποθεσίες",
    "байршил",
    "локации",
    "локацијама",
    "локації",
    "местоположения",
    "урнашкан урыннар",
]


class MySpider(StructuredDataSpider):
    name = "my_spider"
    start_urls = None
    item_attributes = {}
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    matching_links = []

    def parse(self, response):
        for label in LABELS:
            # XPath 2 supports matches(), but we don't have access to it
            # print(response.xpath('//a[matches(text(), "' + label + '", "i")]').get())
            for result in response.xpath(
                '//a[contains(translate(text(), "ABCDEFGHJIKLMNOPQRSTUVWXYZ", "abcdefghjiklmnopqrstuvwxyz"), "'
                + label
                + '")]/@href'
            ).getall():
                self.matching_links.append(result)

        if len(self.matching_links) > 0:
            print("Possible storefinder links")
            for link in set(self.matching_links):
                if "http" not in link:
                    print(self.start_urls[0] + link)
                else:
                    print(link)

        yield


# For a given webpage, examine the human labelled links for possible storefinders
class LinksCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_LEVEL": "WARNING"}

    def syntax(self):
        return "[options] <URL to inspect>"

    def short_desc(self):
        return "Decode a web page or file for structured data with ATP scrapy library code"

    def add_options(self, parser):
        super().add_options(parser)

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify URL to load")

        if args[0].startswith("http"):
            MySpider.start_urls = [args[0]]
        else:
            path = os.path.abspath(args[0])
            MySpider.start_urls = [pathlib.Path(path).as_uri()]

        crawler = self.crawler_process.create_crawler(MySpider, **opts.spargs)
        self.crawler_process.crawl(crawler)
        self.crawler_process.start()
