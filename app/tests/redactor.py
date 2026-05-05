
from app.gaurdrail.pii_redactor import redact


def main() -> None:
    text = "My Aadhaar is 1234 5678 9012, what about yours?"
    
    redacted, summary = redact(text)
    
    print(f"redacted content is : {redacted} \n summary is : {summary}")
    


if __name__ == "__main__":
    main()
    