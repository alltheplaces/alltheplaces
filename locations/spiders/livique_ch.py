import re

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_DE, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class LiviqueCHSpider(SitemapSpider, StructuredDataSpider):
    name = "livique_ch"
    brands = {
        "Livique": "Q15851221",
        "Lumimart": "Q111722218",
    }
    allowed_domains = ["www.livique.ch"]
    sitemap_urls = ["https://www.livique.ch/sitemap.xml"]
    sitemap_follow = ["/STORE-"]
    sitemap_rules = [(r"https://www\.[Ll]ivique\.ch/de/standorte/", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    search_for_phone = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = item["name"]
        brand = name.split()[0].title()
        brand_wikidata = self.brands[brand]
        branch = " ".join(name.split()[1:])

        item["brand"] = item["name"] = brand
        item["brand_wikidata"] = brand_wikidata
        item["country"] = "CH"
        item["branch"] = branch
        item["image"] = self.cleanup_image(item["image"])
        item["lat"], item["lon"] = self.parse_lat_lon(response)
        item["opening_hours"] = self.parse_hours(response)
        item["phone"] = self.cleanup_phone(item["phone"])
        item["ref"] = item["ref"].split("/")[-1].replace("_pos", "")
        item["street_address"] = self.cleanup_street(item["street_address"])
        item["website"] = item["website"].replace("_pos", "_POS")
        yield item

    @staticmethod
    def cleanup_image(image):
        # Some stores have meaningless stock photos of sofas and lamps.
        return image if "POS" in image else None

    @staticmethod
    def cleanup_phone(phone):
        phone = "".join(phone.replace("Tel. 0", "+41").split())
        phone = phone.replace(".", "")
        return phone if re.match(r"^\+41\d{9}$", phone) else None

    @staticmethod
    def cleanup_street(street):
        return street.replace("\u00a0", " ")  # non-breaking space -> space

    @staticmethod
    def parse_hours(response):
        oh = OpeningHours()
        for o in response.xpath("//time/@datetime").extract():
            m = re.match(r"^([A-Z][a-z]), (\d{2}:\d{2})-(\d{2}:\d{2})$", o)
            if m:
                day, open_time, close_time = m.groups()
                oh.add_range(DAYS_DE.get(day), open_time, close_time)
        return oh.as_opening_hours()

    @staticmethod
    def parse_lat_lon(response):
        lat = response.xpath("//meta[@itemprop='latitude']/@content").extract()
        lon = response.xpath("//meta[@itemprop='longitude']/@content").extract()
        return (lat[0], lon[0]) if lat and lon else (None, None)
