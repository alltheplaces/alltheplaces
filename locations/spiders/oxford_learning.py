import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import SocialMedia, set_social_media
from locations.pipelines.address_clean_up import merge_address_lines


class OxfordLearningSpider(Spider):
    name = "oxford_learning"
    item_attributes = {"name": "Oxford Learning", "brand": "Oxford Learning", "brand_wikidata": "Q124034787"}
    start_urls = ["https://www.oxfordlearning.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r"var olc_elements = ({.+});", response.text).group(1))[
            "locationData"
        ].values():
            item = DictParser.parse(location)
            item["addr_full"] = None
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address"], location["address2"]])
            item["ref"] = item["website"]

            if fb := location.get("facebook"):
                set_social_media(item, SocialMedia.FACEBOOK, "https://www.facebook.com/{}".format(fb))
            if twitter := location.get("twitter"):
                set_social_media(item, SocialMedia.TWITTER, "https://twitter.com/{}".format(twitter))

            apply_category(Categories.PREP_SCHOOL, item)

            yield item
