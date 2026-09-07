def consume_user(username: str, age: float, locale: str = "zh-HK") -> dict:
    print("consumer-called")
    return {"accepted": True, "username": username, "age": age, "locale": locale}
