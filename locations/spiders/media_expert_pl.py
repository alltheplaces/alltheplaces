from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class MediaExpertPLSpider(Spider):
    name = "media_expert_pl"

    user_agent = BROWSER_DEFAULT

    custom_settings = {
        # somehow this actually seems to work
        "RETRY_HTTP_CODES": [403],
    }

    requires_proxy = True  # Cloudflare geoblocking in use

    item_attributes = {"brand": "Media Expert", "brand_wikidata": "Q11776794"}

    start_urls = ["https://sklepy.mediaexpert.pl/data/getshops"]
    base_url = "https://sklepy.mediaexpert.pl"

    def parse(self, response: Response):

        for branch in response.json():
            item = DictParser.parse(branch)

            item["ref"] = branch["code"]

            item["street_address"] = item["addr_full"]
            item["addr_full"] = f'{item["street_address"]}, {item["postcode"]} {item["city"]}'

            # sometimes a branch has 2 phone numbers listed, this doesn't get processed properly
            if item.get("phone"):
                item["phone"] = item["phone"].split("\n")[0]

            hour_string = ", ".join(f"{day}: " + branch[f"open_{day.lower()}"] for day in DAYS)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hour_string)

            # "URL" is just a slug
            item["website"] = urljoin(self.base_url, item["website"])
            yield item
