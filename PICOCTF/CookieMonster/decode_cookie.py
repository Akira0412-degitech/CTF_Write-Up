import base64

secret_recpe = "cGljb0NURntjMDBrMWVfbTBuc3Rlcl9sMHZlc19jMDBraWVzXzJDODA0MEVGfQ=="
decoded_bytes = base64.b64decode(secret_recpe)
decoded_str = decoded_bytes.decode('utf-8')

print(decoded_str)