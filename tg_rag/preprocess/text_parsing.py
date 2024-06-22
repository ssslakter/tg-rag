def count_words(text):
    return len(text.split())


def is_dialog(text):
    return text.startswith("-") or text.startswith("–") or text.startswith("—")


def merge_dialogs(paragraphs, max_words=500):
    merged_chunk = []
    result = []
    for p in paragraphs:
        if is_dialog(p) and count_words(" ".join(merged_chunk)) < max_words:
            merged_chunk.append(p)
            continue
        if merged_chunk:
            result.append(" ".join(merged_chunk))
            merged_chunk = []

        if is_dialog(p): merged_chunk.append(p)
        else: result.append(p)
    return result


def merge_short_paragraphs(paragraphs, min_words=50, max_words=500):
    merged_chunk = []
    result = []
    for p in paragraphs:
        if count_words(" ".join(merged_chunk)) >= max_words:
            result.append(" ".join(merged_chunk))
            merged_chunk = []

        if count_words(p) < min_words: merged_chunk.append(p)
        else:
            result.append(" ".join(merged_chunk + [p]))
            merged_chunk = []

    return result


def parse_book(book):
    book = book[book.find("ЧАСТЬ ПЕРВАЯ"):]
    paragraphs = [t for t in book.split("\r\n") if t != '']
    paragraphs = merge_dialogs(paragraphs, 100)
    paragraphs = merge_short_paragraphs(paragraphs, 80, 150)
