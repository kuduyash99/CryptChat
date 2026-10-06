

from app.encryption import encrypt_message, decrypt_message


def main():
    print("=" * 45)
    print("       CRYPTCHAT ENCRYPTION DEMO")
    print("=" * 45)

    message = input("\nEnter a message to encrypt: ")

    if not message.strip():
        print("\nMessage cannot be empty.")
        return

    print("\n[1] ORIGINAL MESSAGE")
    print(message)

    ciphertext, nonce = encrypt_message(message)

    print("\n[2] ENCRYPTED CIPHERTEXT")
    print(ciphertext.hex())

    print("\n[3] RANDOM NONCE")
    print(nonce.hex())

    decrypted = decrypt_message(ciphertext, nonce)

    print("\n[4] DECRYPTED MESSAGE")
    print(decrypted)

    if decrypted == message:
        print("\n✓ AES-256-GCM encryption/decryption successful")
    else:
        print("\n✗ Decryption failed")


if __name__ == "__main__":
    main()