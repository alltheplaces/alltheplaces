from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysAESpider(FiveGuysAUSpider):
    name = "five_guys_ae"
    experience_key = "search-backend-ae"
    locale = (
        "en-AE"  # Using en because it has google attributes which gives lots of extra details (not present in ar-AE)
    )

    def process_websites(self, item) -> None:
        if "/en_ae/" in item["website"]:
            item["extras"]["website:en"] = item["website"]
            item["website"] = item["website"].replace("/en_ae/", "/")
            # Not setting website:ar because it's not guaranteed to be in ar
