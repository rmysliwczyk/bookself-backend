import jwt
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = os.environ["ALGORITHM"]
SECRET_KEY = os.environ["SECRET_KEY"]


def jwt_encode(data: dict, current_time: datetime, exp_delta: timedelta):
    data.update({"exp": current_time + exp_delta})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
