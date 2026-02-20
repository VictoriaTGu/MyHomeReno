def fix_homedepot_url(url):
    """
    If the url is a Home Depot API url (apionline.homedepot.com),
    convert it to a user-facing homedepot.com url.
    """
    if url and 'apionline.homedepot.com/p/' in url:
        return url.replace('apionline.homedepot.com', 'homedepot.com')
    return url
