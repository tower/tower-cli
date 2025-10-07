import os


def main():
    value = os.getenv("PARENT_ENVIRONMENT_VARIABLE", "default_value")
    print(f"The parent environment variable is: {value}")

    value = os.getenv("OVERRIDDEN_ENVIRONMENT_VARIABLE", "default_value")
    print(f"The overridden environment variable is: {value}")

    value = os.getenv("MY_SECRET", "default_value")
    print(f"The secret is: {value}")


if __name__ == "__main__":
    main()
