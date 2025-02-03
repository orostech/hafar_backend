# from cryptography.hazmat.primitives.ciphers.aead import AESGCM
# import os

# class E2EEncryptor:
#     @staticmethod
#     def encrypt_message(sender_key, receiver_public_key, message):
#         # Key exchange using X3DH
#         shared_key = sender_key.exchange(x25519.X25519PublicKey.from_public_bytes(receiver_public_key))
        
#         # AES-GCM encryption
#         nonce = os.urandom(12)
#         cipher = AESGCM(shared_key)
#         ciphertext = cipher.encrypt(nonce, message.encode(), None)
#         return nonce + ciphertext

#     @staticmethod
#     def decrypt_message(receiver_key, sender_public_key, ciphertext):
#         shared_key = receiver_key.exchange(x25519.X25519PublicKey.from_public_bytes(sender_public_key))
#         nonce = ciphertext[:12]
#         encrypted = ciphertext[12:]
#         cipher = AESGCM(shared_key)
#         return cipher.decrypt(nonce, encrypted, None)


from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        response.data = {
            'error': {
                'code': response.status_code,
                'message': response.data
            }
        }
    
    return response