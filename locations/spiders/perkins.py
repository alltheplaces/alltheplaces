import re

import chompjs
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PerkinsSpider(SitemapSpider, StructuredDataSpider):
    name = "perkins"
    item_attributes = {"brand": "Perkins", "brand_wikidata": "Q7169056"}
    allowed_domains = ["www.perkinsrestaurants.com"]
    sitemap_urls = ("https://www.perkinsrestaurants.com/sitemap.xml",)
    sitemap_rules = [
        # Example: https://www.perkinsrestaurants.com/locations/us/mn/winona/956-1-2-mankoto-avenue
        (r"/locations/.*$", "parse_sd")
    ]
    time_format = "%I:%M"
    params_pattern = re.compile(r"function\(([_$\w,\s]+)\)")
    values_pattern = re.compile(r"}\((.+)\)\);")
    stores_pattern = re.compile(r"data:(\[.+\]),fe")
    coordinates_map = {}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        if js := response.xpath('//script[contains(text(), "__NUXT__")]/text()').get():
            latitude_variable = None
            longitude_variable = None

            # A JS Blob contains all of the locations
            # The only one without strings and values will be the current store,
            # which will have variables.
            # We use these to determine what the specific page has compiled, later
            if m := re.search(r"locations:\[(.*)\]", js):
                stores = chompjs.parse_js_object("[" + m.group(1) + "]")
                for store in stores:
                    # Find the one entry with a 2 character variable instead of a URL
                    if len(store["path"]) == 2:
                        latitude_variable = store["content"]["latitude"]
                        longitude_variable = store["content"]["longitude"]

            # See also: ToolstationSpider.
            # stores is actually a JS function, so we have to parse the parameters and values
            params = re.search(self.params_pattern, js).group(1).split(",")
            values = chompjs.parse_js_object("[" + re.search(self.values_pattern, js).group(1) + "]")
            args = {}
            for i in range(0, len(params)):
                args[params[i]] = values[i]

            if latitude_variable is not None and longitude_variable is not None:
                item["lat"] = args[latitude_variable]
                item["lon"] = args[longitude_variable]

            yield item

        return super().post_process_item(item, response, ld_data, **kwargs)
