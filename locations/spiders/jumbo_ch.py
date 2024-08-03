import re

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class JumboCHSpider(SitemapSpider):
    name = "jumbo_ch"
    item_attributes = {
        "brand": "Jumbo",
        "brand_wikidata": "Q1713190",
        "country": "CH",
    }
    allowed_domains = ["www.jumbo.ch"]
    sitemap_urls = ["https://www.jumbo.ch/sitemap.xml"]
    sitemap_follow = ["/sitemap/STORE-de-"]
    sitemap_rules = [(r"_POS$", "parse_store")]

    def parse_store(self, response):
        # Not using StructuredDataSpider because the site supplies *two*
        # linked data items of type LocalBusiness. The first contains
        # the branch name, the second all the other properties.
        MicrodataParser.convert_to_json_ld(response)
        ld_items = [o for o in LinkedDataParser.iter_linked_data(response) if o.get("@type") == "LocalBusiness"]
        if len(ld_items) < 2:
            return
        branch = LinkedDataParser.parse_ld(ld_items[0])["name"].strip()
        for prefix in ("JUMBO Maximo", "JUMBO"):
            branch = branch.removeprefix(prefix).strip()
        item = LinkedDataParser.parse_ld(ld_items[1])
        ref = re.search(r"/([0-9]+)_POS$", response.url).group(1)
        item.update(
            {
                "branch": branch,
                "image": "https://www.jumbo.ch/img/vst/pos833Wx555H/%s_POS.jpg" % ref,
                "name": "Jumbo",
                "opening_hours": self.parse_hours(response),
                "phone": item["phone"].strip().removeprefix("Tel.:").strip(),
                "ref": ref,
                "website": response.url,
            }
        )
        if m := re.match(r"^(\d{4}) (.+)$", item["city"]):
            item["postcode"], item["city"] = m.groups()
        yield item

    @staticmethod
    def parse_hours(response):
        oh = OpeningHours()
        table = response.css("table.store-openings")
        days, hours = table.xpath("//th/text()"), table.xpath("//td/text()")
        for day, hour in zip(days.getall(), hours.getall()):
            day = day.strip().removesuffix("(Heute)").strip()
            if m := re.match(r"^(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})$", hour):
                open_time, close_time = m.groups()
                oh.add_range(DAYS_DE.get(day), open_time, close_time)
        return oh
