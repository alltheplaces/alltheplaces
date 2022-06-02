import json
import re

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class GameSpider(SitemapSpider):
    name = "game"
    item_attributes = {"brand": "Game", "brand_wikidata": "Q5519813", "country": "GB"}
    located_in_brands = {
        "Frasers": "Q5928422",
        "House of Fraser": "Q5928422",
        "Sports Direct": "Q7579661",
    }
    allowed_domains = ["storefinder.game.co.uk"]
    sitemap_urls = ["https://storefinder.game.co.uk/sitemap.xml"]
    download_delay = 2
    custom_settings = {"DOWNLOAD_TIMEOUT": 10}

    def sitemap_filter(self, entries):
        for entry in entries:
            if not entry["loc"] in [
                "https://storefinder.game.co.uk/game/stores/search",
                "https://storefinder.game.co.uk/game/stores/2216/Londonderry/Derry",
            ]:
                yield entry

    def parse(self, response):
        ld = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )
        store = GeojsonPointItem()
        store["lat"] = ld["geo"]["latitude"]
        store["lon"] = ld["geo"]["longitude"]
        store["name"] = ld["name"].strip()
        store["street_address"] = (
            ld["address"]["streetAddress"]
            .replace(", ,", ", ")
            .replace(",,", ",")
            .replace(" ,", ",")
            .replace("  ", " ")
            .replace("GAME", "")
            .replace("Game", "")
            .strip(" ,")
        )
        store["city"] = ld["address"]["addressLocality"].replace("  ", " ").strip()
        store["state"] = ld["address"]["addressRegion"]
        store["postcode"] = ld["address"]["postalCode"]
        store["website"] = response.url

        twitter = response.xpath('//meta[@name="twitter:site"]/@content').get().strip()
        if twitter != "@GAMEdigital":
            store["twitter"] = twitter

        store["opening_hours"] = (
            ld["openingHours"][0]
            .replace("Mo-Fri ", "Mo-Fr ")
            .replace(", ", "; ")
            .replace('"', "")
            .replace("`", "")
        )
        store["ref"] = response.url.split("/")[5]

        img = response.xpath('//meta[@name="twitter:image"]/@content').get()
        if img != "https://cdn.game.net/image/upload/":
            store["image"] = img

        # Normalise a couple of exceptions
        store["street_address"] = (
            store["street_address"]
            .replace("sports Direct", "Sports Direct")
            .replace("SportsDirect", "Sports Direct")
            .replace("Sports Direct 1st Floor", "Sports Direct, 1st Floor")
            .replace("Sports Direct Unit F2", "Sports Direct, Unit F2")
            .replace("Sports Direct DW", "Sports Direct")
            .replace("Sports Direct Middlesbrough Linth", "Sports Direct")
            .replace("Sports Direct, Frasers", "House of Fraser")
            .replace("House Of Fraser", "House of Fraser")
        )
        located_in = re.match("(?i)c\/o ([\w ]+), (.+)", store["street_address"])
        if located_in:
            store["located_in"] = located_in.group(1)
            store["located_in_wikidata"] = self.located_in_brands.get(
                located_in.group(1)
            )
            store["street_address"] = located_in.group(2)

        yield store
