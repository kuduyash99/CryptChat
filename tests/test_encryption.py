from app.encryption import encrypt_message, decrypt_message


message = "Hello from CryptChat!"

ciphertext, nonce = encrypt_message(message)

print("Encrypted:", ciphertext)
print("Nonce:", nonce)

decrypted = decrypt_message(ciphertext, nonce)

print("Decrypted:", decrypted)

assert decrypted == message

print("Encryption test successful")