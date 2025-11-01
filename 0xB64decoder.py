from base64 import b64decode


encoded_string = input("base64 encoded: ")

# decode the string
decoded_string = b64decode(encoded_string)

print(decoded_string)