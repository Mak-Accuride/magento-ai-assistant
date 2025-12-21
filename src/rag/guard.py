def is_confident_enough(docs, min_docs=2):
    return len(docs) >= min_docs

def is_relevant_enough(docs, min_docs=1):
    return len(docs) >= min_docs
