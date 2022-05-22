from locations.google_url import url_to_coords


def tests():
    assert url_to_coords(
        "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2421.2988280554714!2d1.2830013158163067!3d52.636513979836515!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47d9e161f2318f3f%3A0x1011fac48e8edcbf!2sNorwich+Depot+-+Parcelforce+Worldwide!5e0!3m2!1sen!2sus!4v1496935482694"
    ) == (52.636513979836515, 1.2830013158163067)
    assert url_to_coords(
        "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2500.3404587315936!2d0.2883177157631218!3d51.1943779795849!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47df48b0a94080d3%3A0xa460c3bddd378d92!2sTonbridge+Depot+-+Parcelforce+Worldwide!5e0!3m2!1sen!2sus!4v1496934862229"
    ) == (51.1943779795849, 0.2883177157631218)


if __name__ == "__main__":
    tests()
    print("Everything passed")
