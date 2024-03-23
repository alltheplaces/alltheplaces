import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PoieszSupermarktenNLSpider(SitemapSpider, StructuredDataSpider):
    name = "poiesz_supermarkten_nl"
    item_attributes = {"brand": "Poiesz Supermarkten", "brand_wikidata": "Q2521700"}
    sitemap_urls = ["https://www.poiesz-supermarkten.nl/sitemap.xml"]
    sitemap_rules = [(r"https://www.poiesz-supermarkten.nl/onze-winkels/.*$", "parse_sd")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # <script type="text/javascript">
        #      $(function() {
        #      Poiesz.GoogleMaps.addStore({lat:53.281669,lng:6.153749});Poiesz.GoogleMaps.initHeaderStores();});
        #   </script>
        coordinates_fragment = response.xpath("//script[contains(text(), 'lat:')]/text()").get()
        if coordinates_fragment:
            if m := re.search(r"lat:(-?\d+\.\d+),lng:(-?\d+\.\d+)", coordinates_fragment):
                item["lat"] = m.group(1)
                item["lon"] = m.group(2)

        yield from self.inspect_item(item, response)
