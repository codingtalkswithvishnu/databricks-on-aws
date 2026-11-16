"""Preserve named policy fields from the optional AI Search response."""

POLICY_FIELDS = ("article_id", "version", "effective_from", "owner", "status", "title", "body")


def policy_hits(payload):
    try:
        columns = payload["manifest"]["columns"]
        names = [column["name"] for column in columns]
        rows = payload["result"].get("data_array", [])
        if (len(names) != len(set(names)) or not set(POLICY_FIELDS).issubset(names)
                or not isinstance(rows, list) or len(rows) > 2):
            raise ValueError("Unsupported search response")
        documents = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < len(names):
                raise ValueError("Unsupported search row")
            named = dict(zip(names, row))
            if any(not isinstance(named[key], str) or not named[key].strip() for key in POLICY_FIELDS):
                raise ValueError("Policy content/metadata is missing")
            documents.append({key:named[key] for key in POLICY_FIELDS})
        return documents
    except (KeyError, TypeError, AttributeError, ValueError):
        raise ValueError("Unsupported policy-search response") from None
