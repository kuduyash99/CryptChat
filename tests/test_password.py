import bcrypt


def main():
    print("=" * 45)
    print("        CRYPTCHAT BCRYPT DEMO")
    print("=" * 45)

    password = input("\nEnter a password: ")

    if not password:
        print("\nPassword cannot be empty.")
        return

    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    print("\n[1] ENTERED PASSWORD")
    print(password)

    print("\n[2] BCRYPT HASH STORED IN DATABASE")
    print(hashed.decode("utf-8"))

    print("\n[3] VERIFY PASSWORD")
    check = input("Enter password again: ")

    if bcrypt.checkpw(check.encode("utf-8"), hashed):
        print("\n✓ Password verification successful")
    else:
        print("\n✗ Password verification failed")


if __name__ == "__main__":
    main()