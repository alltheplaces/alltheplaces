import re

import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class WaitroseSpider(scrapy.Spider):
    name = "waitrose"
    LITTLE_WAITROSE = {"brand": "Little Waitrose", "brand_wikidata": "Q771734"}
    WAITROSE = {"brand": "Waitrose", "brand_wikidata": "Q771734"}
    item_attributes = WAITROSE
    allowed_domains = ["www.waitrose.com"]
    bf_home = "http://www.waitrose.com/content/waitrose/en/bf_home"
    start_urls = (bf_home + "/bf.html",)
    requires_proxy = True

    def parse(self, response):
        # if this is a store details page then it will have the following
        # div section.
        details = response.xpath('//div[@role="article"]/div' '/div[@class="parbase details section"]')

        if details:
            name = response.xpath("//head/title/text()").get()
            # sometimes, but not always, the name of the shop also has some
            # variant of " - Branch Finder..." appended. the fact that it's
            # not consistent between pages seems to indicate that it has been
            # entered by hand.
            name = re.sub(r"Welcome to|Branch Finder|Waitrose.com", "", name, flags=re.IGNORECASE).strip(" -")

            properties = {
                "name": name,
                "website": response.url,
                "ref": response.meta["waitrose_store_id"],
            }

            if "little waitrose" in name.lower():
                properties.update(self.LITTLE_WAITROSE)
                apply_category(Categories.SHOP_CONVENIENCE, properties)
            else:
                properties.update(self.WAITROSE)
                apply_category(Categories.SHOP_SUPERMARKET, properties)

            branch_details = details[0].xpath('div[@class="col branch-details"]/p')[0].root.text_content()
            if branch_details:
                branch_details = self._branch_details(branch_details)
            if branch_details:
                properties.update(branch_details)

            opening_hours = details[0].xpath('div[@class="opening-times"]')[0]
            if opening_hours:
                properties["opening_hours"] = self._opening_hours(opening_hours)

            branch_map = details[0].xpath('div[@class="branch-finder-map"]/p/a')[0].root.attrib
            properties.update(
                {
                    "lon": float(branch_map["data-long"]),
                    "lat": float(branch_map["data-lat"]),
                }
            )

            yield Feature(**properties)
            return

        # otherwise it's the top-level store page
        #
        # the Waitrose store selector starts with a drop-down box of options,
        # some of which are associated with store IDs and some of which are
        # blank for instructions or other comments.
        selector = '//select[@id="global-form-select-branch"]/option/@value'
        store_options = response.xpath(selector).extract()

        # filter out the store IDs from the other junk in the value field.
        store_ids = []
        for option in store_options:
            try:
                store_id = int(option)
                store_ids.append(store_id)
            except ValueError:
                pass

        for store_id in store_ids:
            url = "%s/bf/%d.html" % (WaitroseSpider.bf_home, store_id)
            yield scrapy.Request(url, meta=dict(waitrose_store_id=store_id))

        return

    def _branch_details(self, branch_details):
        lines = []
        # branch details are given as <br>-separated lines, rather than
        # marked up in useful way. this makes it harder to extract information
        # about the store :-(
        for line in branch_details.splitlines():
            text = line.strip()
            if text:
                lines.append(text)

        properties = {}

        # last line is usually, but not always, a phone number.
        line = lines[-1]
        if re.match("0[0-9 ]+", line):
            properties["phone"] = line
            lines.pop()

        # the next-to-last (or last when there's no phone) is usually a
        # post code.
        line = lines[-1]
        if re.match("[A-Z0-9]+ [A-Z0-9]+", line):
            properties["postcode"] = line
            lines.pop()

        # TODO: some Waitrose stores are not in the UK, and have the country
        # name as the final line, e.g: there are a few in the UAE.
        # unfortunately, there's at least one in the UAE which doesn't include
        # a country, so a better way to find the country might be to reverse
        # lookup the latlon.

        # if the first line is a number and name, then it's probably a house
        # number and street name.
        line = lines[0]
        m = re.match("([0-9-]+) ([A-Za-z ]+)", line)
        if m:
            properties["housenumber"] = m.group(1)
            properties["street"] = m.group(2)

        properties["addr_full"] = ", ".join(lines)
        return properties

    def _opening_hours(self, opening_hours: Selector) -> OpeningHours:
        oh = OpeningHours()
        for row in opening_hours.xpath("//tr"):
            day, times = row.xpath("td/text()").extract()
            times = times.replace(" ", "")
            if times == "CLOSED":
                continue
            day = sanitise_day(day.strip(":"))
            if not day:
                continue
            start_time, end_time = times.split("-")
            oh.add_range(day, start_time, end_time)
        return oh
