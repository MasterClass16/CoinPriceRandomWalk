from sanic import Sanic
import numpy as np
from sanic.response import json as sanicjson
import redis
import os


def bounded_random_walk(length, lower_bound,  upper_bound, start, end, std):
    assert (lower_bound <= start and lower_bound <= end)
    assert (start <= upper_bound and end <= upper_bound)

    bounds = upper_bound - lower_bound

    rand = (std * (np.random.random(length) - 0.5)).cumsum()
    rand_trend = np.linspace(rand[0], rand[-1], length)
    rand_deltas = (rand - rand_trend)
    rand_deltas /= np.max([1, (rand_deltas.max()-rand_deltas.min())/bounds])

    trend_line = np.linspace(start, end, length)
    upper_bound_delta = upper_bound - trend_line
    lower_bound_delta = lower_bound - trend_line

    upper_slips_mask = (rand_deltas-upper_bound_delta) >= 0
    upper_deltas =  rand_deltas - upper_bound_delta
    rand_deltas[upper_slips_mask] = (upper_bound_delta - upper_deltas)[upper_slips_mask]

    lower_slips_mask = (lower_bound_delta-rand_deltas) >= 0
    lower_deltas =  lower_bound_delta - rand_deltas
    rand_deltas[lower_slips_mask] = (lower_bound_delta + lower_deltas)[lower_slips_mask]

    return trend_line + rand_deltas

r = redis.StrictRedis(
host=os.getenv('REDIS_ENDPOINT'),
port= os.getenv('REDIS_PORT'),
password=os.getenv('REDIS_PASS'),
charset="utf-8",
decode_responses=True)

app = Sanic(name='AlphOne')

@app.route('/')
@app.route('/<path:path>')
async def index(request, path=""):
    if r.exists('prices'):
        current = r.rpop('prices')
    else:
        random_data = bounded_random_walk(20, lower_bound=0.6, upper_bound =1.4, start=1, end=1, std=0.3).tolist()
        current = random_data.pop(0)
        r.lpush('prices', *random_data)
    return sanicjson(current)



if __name__ == '__main__':
    app.run()