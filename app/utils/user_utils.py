def trim_full_link(link):
    if "profile.php" in link:
        return link.split("&")[0]
    else:
        return link.split("?")[0]
