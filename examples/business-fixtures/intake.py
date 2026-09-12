def collect_booking_request(name: str, phone: str, service: str, slot: str, notes: str = "") -> dict:
    """模拟一个旧预约表单的输出；不访问网络，不写外部系统。"""
    return {
        "name": name,
        "phone": phone,
        "service": service,
        "slot": slot,
        "notes": notes,
        "debug_source": "legacy-booking-form",
    }
