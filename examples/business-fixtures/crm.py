def create_crm_lead(
    customer_name: str,
    phone: str,
    service_code: str,
    preferred_time: str,
    notes: str = "",
    channel: str = "web",
) -> dict:
    """模拟 CRM 接收一条预约线索；不访问真实 CRM。"""
    return {
        "accepted": True,
        "customer_name": customer_name,
        "phone": phone,
        "service_code": service_code,
        "preferred_time": preferred_time,
        "notes": notes,
        "channel": channel,
    }
