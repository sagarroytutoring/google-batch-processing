from urllib import request


def in_google_cloud() -> bool:
    url = "http://metadata.google.internal/"
    try:
        request.urlopen(
            request.Request(url, headers={"Metadata-Flavor": "Google"})
        ).read().decode()
        return True
    except Exception:
        return False


ON_GCP = in_google_cloud()
