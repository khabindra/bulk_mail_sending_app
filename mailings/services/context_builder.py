def build_email_context(client, sender, message, request_data=None):
    request_data = request_data or {}

    context = {
        "company_name": client.company_name,
        "contact_email": client.contact_email,
        "message": message,
        "sender_name": sender.name,
        "sender_email": sender.email,
    }

    # Allow only explicitly prefixed variables
    for key, value in request_data.items():
        if key.startswith("var_"):
            context[key] = value

    return context
