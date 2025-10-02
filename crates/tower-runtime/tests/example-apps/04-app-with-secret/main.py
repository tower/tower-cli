import os


def main():
    value = os.getenv("MY_SECRET", "default_value")
    print(f"The secret is: {value}")


if __name__ == "__main__":
    main()
