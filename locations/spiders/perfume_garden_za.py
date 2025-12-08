from scrapy import Selector, Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class PerfumeGardenZASpider(Spider):
    name = "perfume_garden_za"
    start_urls = ["https://www.perfumegarden.co.za/pages/store-locator"]
    item_attributes = {
        "brand": "The Perfume Garden",
        "brand_wikidata": "Q116462359",
    }
    no_refs = True

    def parse(self, response):
        for section in response.xpath('.//p[@style="text-align: left;"]'):
            for line in section.get().split("<br>"):
                if "<span>" in line:
                    line = Selector(text=line).xpath("string(.)").get()
                if line.strip() == "":
                    continue
                if "KZN STORES" in line or "CPT STORES" in line:
                    continue
                if "<b>" in line or "<strong>" in line:
                    item = Feature()
                    if branch := Selector(text=line).xpath(".//b/text()").get():
                        pass
                    else:
                        branch = Selector(text=line).xpath(".//strong/text()").get()
                    item["branch"] = branch.strip()
                elif "Shop" in line:
                    if "Tel:" in line:
                        tels = line.split("Shop")[0]
                        item["phone"] = "; ".join(tels.replace("Tel:", "").split("|"))
                        line = "Shop" + line.split("Shop")[1]
                    item["addr_full"] = clean_address(line)
                    try:
                        postcode_guess = item["addr_full"].split(",")[-1]
                        int(postcode_guess)
                        item["postcode"] = postcode_guess
                    except:
                        pass
                elif "Tel:" in line:
                    item["phone"] = "; ".join(line.replace("Tel:", "").split("|"))
                elif "Trading Hours" in line:
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_ranges_from_string(line)
                    yield item
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_line/{line}")
