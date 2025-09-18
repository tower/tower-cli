from faker import Faker


def main():
    fake = Faker()
    print(fake.name())


if __name__ == "__main__":
    main()
