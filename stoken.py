from itsdangerous import URLSafeTimedSerializer
from key import secret_key
import os
def token(email,salt):
    serializer= URLSafeTimedSerializer(secret_key)
    #serializer= URLSafeTimedSerializer(os.urandom(45))
    #token=serializer.dumps('tatababitha366@gmail.com',salt='confirmation')
    #return serializer.dumps('tatababitha366@gmail.com',salt='confirmation')
    return serializer.dumps(email,salt=salt)
 
'''print(token)
print(serializer.loads(token,salt='confirmation',max_age=120))
from key import secret_key,salt'''