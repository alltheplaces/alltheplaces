import json
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PompeaITSpider(StructuredDataSpider):
    name = "pompea_it"
    item_attributes = {"brand": "Pompea", "brand_wikidata": "Q130729934", "name": "Pompea"}
    start_urls = ["https://www.pompea.com/pages/i-nostri-store"]
    wanted_types = ["LocalBusiness"]
    # Without an explicit Italian Accept-Language, Shopify Markets redirects to
    # a machine-translated /en/ page whose store names no longer match those in
    # the page's JSON-LD (e.g. "Spaccio Asola" becomes "Buttonholes Store").
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept-Language": "it"}}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Coordinates are not present in the page's JSON-LD, only in the map
        # widget's marker inputs, which appear in the same order as the
        # matching accordion entries used for name/address/phone/email.
        coordinates_by_branch = {}
        seen_coordinates = set()
        duplicate_coordinates = set()
        for pin, summary in zip(
            response.css("input.thb-location"),
            response.css("google-map details summary"),
        ):
            option = json.loads(pin.attrib["data-option"])
            name = summary.css("::text").get().strip().upper()
            coordinates = (option["latitude"], option["longitude"])
            coordinates_by_branch[name] = coordinates
            if coordinates in seen_coordinates:
                duplicate_coordinates.add(coordinates)
            seen_coordinates.add(coordinates)

        # The site's own map widget reuses one pair of coordinates for two
        # different outlets (Asola and Franciacorta), so neither can be
        # trusted; drop coordinates for any branch caught up in that clash.
        self.coordinates_by_branch = {
            name: coordinates
            for name, coordinates in coordinates_by_branch.items()
            if coordinates not in duplicate_coordinates
        }

        yield from super().parse(response, **kwargs)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes(Clothes.UNDERWEAR, item)

        branch = item.pop("name")
        item["branch"] = branch
        item["ref"] = branch

        if coordinates := self.coordinates_by_branch.get(branch.upper()):
            item["lat"], item["lon"] = coordinates

        yield item
