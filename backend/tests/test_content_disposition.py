from routers.assets import _inline_disposition


def test_inline_disposition_keeps_the_fallback_name_in_printable_ascii():
    header = _inline_disposition('salon\nnotes "black" שיער.txt')

    assert header.startswith("inline; filename=\"salon?notes black ????.txt\"; filename*=UTF-8''")
    assert all(" " <= character <= "~" for character in header)


def test_inline_disposition_keeps_a_plain_name_as_is():
    header = _inline_disposition("photo one.jpg")

    assert header == "inline; filename=\"photo one.jpg\"; filename*=UTF-8''photo%20one.jpg"
