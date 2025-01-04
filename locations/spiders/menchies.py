import re
import scrapy

from locations.google_url import url_to_coords
from locations.items import Feature
from locations.hours import OpeningHours
from locations.categories import Extras, apply_yes_no
from locations.pipelines.address_clean_up import merge_address_lines


class MenchiesSpider(scrapy.Spider):
    name = "menchies"
    allowed_domains = ["menchies.com"]
    start_urls = ["https://www.menchies.com/all-locations"]
    item_attributes = {
        "brand": "Menchie's",
        "brand_wikidata": "Q6816528",
    }

    def parse(self, response):
        locs = response.css(".loc-info")
        for loc in locs:
            if loc.css(".coming-soon"):
                continue

            item = Feature()
            # At least one location has a broken Google Maps link
            try:
                google_maps_url = loc.css(".loc-directions a::attr(href)").get()
                item["lat"], item["lon"] = url_to_coords(google_maps_url)
            except:
                pass

            # The fav-* class is the store number
            fav_class = loc.css(".favorite::attr(class)").get().split()[-1]
            ref = fav_class.split("-")[1]
            item["ref"] = ref

            # name = loc.css(".loc-name a::text").get()

            website = loc.css(".loc-name a::attr(href)").get()
            item["website"] = response.urljoin(website)

            addr = loc.css(".loc-address::text").getall()
            item["addr_full"] = merge_address_lines(addr)

            phone = loc.css(".loc-phone a::attr(href)").get()
            if phone:
                item["phone"] = phone

            oh = OpeningHours()
            for hours in loc.css(".loc-hours::text").getall():
                oh.add_ranges_from_string(hours)
            item["opening_hours"] = oh.as_opening_hours()

            # If a location's social media account is unavailable, this page links the brand's account
            for url in loc.css(".loc-sm-icons a::attr(href)").getall():
                if "facebook" in url and "mymenchies" not in url.lower():
                    item["facebook"] = url
                if "instagram" in url and "mymenchies" not in url.lower():
                    item["extras"]["contact:instagram"] = url
                if "twitter" in url and "mymenchies" not in url.lower():
                    url = url.replace("#!/", "")
                    item["twitter"] = url

            buttons = loc.css(".loc-green-buttons")
            delivery = buttons.css("a[text='Delivery']")
            if delivery:
                apply_yes_no(Extras.DELIVERY, item, True)

            yield item
