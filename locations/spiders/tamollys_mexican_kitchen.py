import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# The chain's name, with which every restaurant's own name begins.
CHAIN = "TaMolly's Mexican Kitchen"


class TamollysMexicanKitchenSpider(SitemapSpider, StructuredDataSpider):
    """Every page the sitemap lists is read, and those describing a restaurant
    state it in full as linked data: its address, its position, its telephone
    number and the hours it keeps.

    The pages are told apart by what they carry rather than by their address,
    because a restaurant's page sits at the top of the site beside the menu and
    the careers page and is shaped no differently. A restaurant opened later is
    found without the spider being touched.

    The locations page lists a seventh restaurant, which is the chain's head
    office under the office's own address rather than a restaurant's. It is not
    taken: it is written inside that page's list of items rather than at the
    top of its linked data, which is as deep as the reading goes.
    """

    name = "tamollys_mexican_kitchen"
    # Neither the chain nor any of its restaurants has a Wikidata item.
    item_attributes = {"brand": CHAIN}
    allowed_domains = ["tamollys.com"]
    sitemap_urls = ["https://tamollys.com/sitemap.xml"]
    sitemap_rules = [(r"tamollys\.com/", "parse_sd")]
    wanted_types = ["Restaurant"]
    # The only picture any restaurant carries is the chain's own, and the only
    # account on X is the chain's. Each does link its own page on Facebook,
    # which the linked data states and which is taken from there.
    search_for_image = False
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        # The linked data names each restaurant after its own page, with a
        # fragment behind it that the page address already carries.
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]

        # Each restaurant is named for its town, behind the chain's name, and
        # names its state after it, which the address states already.
        branch = (item.pop("name", None) or "").removeprefix(CHAIN).strip(" -")
        if state := item.get("state"):
            branch = re.sub(rf",\s*{re.escape(state)}$", "", branch)
        item["branch"] = branch or None

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "mexican;tex-mex"
        yield item
