def npr_processor(soup):
    return (
        a_link
        for section in soup.find_all("div", class_="topic-container")
        for a_link in section.find_all("a")
    )


def generic_processor(soup):
    return (
        a_link
        for section in soup.find_all("section")
        for a_link in section.find_all("a")
    )
