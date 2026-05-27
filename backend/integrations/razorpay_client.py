import razorpay


def build_razorpay_client(key_id: str, key_secret: str) -> razorpay.Client:
    return razorpay.Client(auth=(key_id, key_secret))

