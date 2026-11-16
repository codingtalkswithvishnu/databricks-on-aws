"""Small response adapter for the optional aggregate-only Genie chat example."""


def summarize_genie_message(payload):
    if not isinstance(payload, dict) or payload.get("status") != "COMPLETED":
        raise RuntimeError("Genie message has not completed successfully")
    message_id = payload.get("message_id") or payload.get("id")
    conversation_id = payload.get("conversation_id")
    if not all(isinstance(value, str) and value for value in (message_id, conversation_id)):
        raise ValueError("Genie response is missing its conversation/message identifiers")
    attachments = payload.get("attachments") or []
    if not isinstance(attachments, list) or len(attachments) > 8:
        raise ValueError("Unsupported attachment collection for the learning adapter")
    texts, queries = [], []
    for attachment in attachments:
        if not isinstance(attachment, dict):
            raise ValueError("Unsupported Genie attachment")
        text = attachment.get("text")
        if text is not None:
            if (not isinstance(text, dict) or not isinstance(text.get("content"), str)
                    or len(text["content"]) > 20000):
                raise ValueError("Unsupported Genie text attachment")
            texts.append(text["content"])
        query = attachment.get("query")
        if query is not None:
            attachment_id = attachment.get("attachment_id")
            if (not isinstance(query, dict) or not isinstance(query.get("query"), str)
                    or not isinstance(attachment_id, str) or not attachment_id
                    or len(query["query"]) > 20000):
                raise ValueError("Unsupported Genie query attachment")
            queries.append({"attachment_id":attachment_id, "sql":query["query"]})
    if not texts and not queries:
        raise ValueError("No supported text/query attachment in the completed response")
    return {"conversation_id":conversation_id, "message_id":message_id,
            "texts":texts, "queries":queries}
