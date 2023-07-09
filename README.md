# lcauto

Python script to auto-submit leetcode questions.

## Why

I like the leetcode 'random question' function, but easy and medium questions started to get too easy and spammy for me.

However, there is no good way of filtering them like on better websites like codeforces or atcoder.

So I wrote this script to help me auto-submit easy/medium questions, so that they will not appear as random questions anymore.

It just prints solutions to-be-submitted. I sometimes try to figure out the problem from the solution, which is a fun reverse-challenge.


## How to use

1. Inspect any logged-in request to leetcode.com, copy the 'Cookie' text value under 'Request Headers', export as `export COOKIE='csrftoken=...; _gat=1'`
2. Activate venv `. .venv/bin/activate`, onetime setup: `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
3. Run `python3 main.py`

## Options
* `CONFIRM=1` to review solutions before submitting, skipping questions
* `MEDIUM=1` to also submit Medium questions, not just Easy
* `NOCOMPILE=1` to skip the sanity-check g++ compile step
 
## Limitations

Only works for problems where shared valid C++ solutions are available and tagged.

## TODO

Right now it just filters problems that have no solutions in the code, you can probably filter those out in the graphql query.
