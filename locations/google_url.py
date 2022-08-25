from urllib.parse import urlparse, parse_qs


def extract_google_position(item, response):
    for link in response.xpath("//img/@src").extract():
        if link.startswith("https://maps.googleapis.com/maps/api/staticmap"):
            item["lat"], item["lon"] = url_to_coords(link)
            return


def url_to_coords(url: str) -> (float, float):
    def get_query_param(link, query_param):
        parsed_link = urlparse(link)
        queries = parse_qs(parsed_link.query)
        return queries.get(query_param)

    if url.startswith("https://www.google.com/maps/embed?pb="):
        # https://andrewwhitby.com/2014/09/09/google-maps-new-embed-format/
        params = url[38:].split("!")

        for i in range(0, len(params)):
            if params[i] == "1m3":
                lat = 0
                lon = 0

                for k in range(i + 1, i + 4):
                    if params[k][:2] == "2d":
                        lon = float(params[k][2:])
                    elif params[k][:2] == "3d":
                        lat = float(params[k][2:])

                return lat, lon
    elif url.startswith("https://maps.googleapis.com/maps/api/staticmap"):
        ll = get_query_param(url, "center")
        if ll:
            lat, lon = ll[0].split(",")
            return float(lat), float(lon)
    elif url.startswith("https://www.google.com/maps/@"):
        lat, lon, _ = url.replace("https://www.google.com/maps/@", "").split(",")
        return float(lat), float(lon)
    elif url.startswith("https://www.google.com/maps/dir/"):
        lat, lon = url.split("/")[6].split(",")
        return float(lat.strip()), float(lon.strip())

    if "/maps.google.com/" in url:
        ll = get_query_param(url, "ll")
        if ll:
            lat, lon = ll[0].split(",")
            return float(lat), float(lon)

    return None, None
