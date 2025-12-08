from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysATSpider(FiveGuysAUSpider):
    name = "five_guys_at"
    experience_key = "search-backend-at"
    locale = "de-AT"  # Using de because it has google attributes which gives lots of extra details (not present in en)

    def process_websites(self, item) -> None:
        item["extras"]["website:de"] = item["website"]
        item["extras"]["website:en"] = item["website"].replace("fiveguys.at/", "fiveguys.at/en_at/")
