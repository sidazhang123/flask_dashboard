from passlib.hash import sha256_crypt
p1=sha256_crypt.encrypt("dazar123")
p2=sha256_crypt.encrypt("dazar123")
print(p1)
print(sha256_crypt.verify('dazar123',p1))
