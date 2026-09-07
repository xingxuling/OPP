def produce_user(user_name: str, age: int) -> dict:
    print("producer-called")
    return {"user_name": user_name, "age": age, "debug": True}
