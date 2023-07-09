import os
import random
import re
import requests
import shutil
import subprocess
import tempfile
import time

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/114.0'.encode(),
    'Cookie': os.getenv('COOKIE').encode(),
    'x-csrftoken': re.search(r'csrftoken=(\w+)', os.getenv('COOKIE')).group(1).encode(),
    'Referer': 'https://leetcode.com/'.encode()
}


def solve(slug: str, qid: str) -> None:
    print(f"Trying to solve {slug}.")
    body = {
        "query": "\n    query communitySolutions($questionSlug: String!, $skip: Int!, $first: Int!, $query: String, $orderBy: TopicSortingOption, $languageTags: [String!], $topicTags: [String!]) {\n  questionSolutions(\n    filters: {questionSlug: $questionSlug, skip: $skip, first: $first, query: $query, orderBy: $orderBy, languageTags: $languageTags, topicTags: $topicTags}\n  ) {\n    hasDirectResults\n    totalNum\n    solutions {\n      id\n      title\n      solutionTags {\n        name\n        slug\n      }\n      post {\n        id\n           voteCount\n       content\n        author {\n          username\n      }\n      }\n    }\n  }\n}\n    ",
        "variables": {"query": "", "languageTags": [], "topicTags": [],
                      "questionSlug": slug, "skip": 0, "first": 100,
                      "orderBy": "most_votes"}, "operationName": "communitySolutions"}
    response = requests.get("https://leetcode.com/graphql/", json=body)
    if response.status_code != 200:
        print(f"Failed to fetch graphql solution content, status: {response.status_code}. Skipping.")
        return
    if response.status_code == 429:
        print("Got rate limited while fetching solutions, sleeping for 10 seconds to try again.")
        time.sleep(10)
        solve(slug, qid)
        return

    if not response.json()['data']['questionSolutions']['hasDirectResults']:
        print("Does not have any solutions. Skipping.")
        return

    for solution in response.json()['data']['questionSolutions']['solutions']:
        if "cpp" not in [tag['slug'] for tag in solution['solutionTags']]:
            continue
        # Extract text part in ``` ... ``` code block.
        matched_tag = re.search(r"```((.(?!```))+.)```", solution['post']['content'])
        if not matched_tag:
            # Else don't bother trying to extract it from freeform text
            continue
        if submit_code(matched_tag.group(1), qid):
            break


# True -> done with questions
# False -> try next solution
def submit_code(code: str, qid: str) -> bool:
    # sanitize common error patterns
    if code[:2] == "\\n":
        code = code[2:]
    if code[:3].lower() == 'cpp':
        code = code[3:]
    if code.startswith("C++ []"):
        code = code[6:]
    if re.match(r"^\s*'", code) and re.match(r".*'\s*$"):
        code = code[code.index("'") + 1:len(code) - code[::-1].index("'") - 1]
    if re.search(r"class [A-Z]\w+:", code):
        print(f"maybe Python, skipping:\n {code}")
        return False
    if not re.search(r"public\s*:", code) or re.search(r"public (String|int|Integer)", code):
        print(f"no main or maybe Java, skipping:\n {code}")
        return False
    if not re.search(r"class [A-Z]\w+", code):
        print(f"did not have main class, skipping:\n {code}")
        return False
    if code.count("class Solution") >= 2:
        print(f"multiple options, skipping:\n {code}")
        return False

    # unescape single quotes, whitespace
    code = re.sub(r'\\n', '\n', code)
    code = re.sub(r'\\t', '\t', code)
    code = re.sub(r"\\", "", code)

    if not os.getenv('NOCOMPILE') and not can_compile(code):
        print("Could not compile. Skipping.")
        return False

    print(f"Code to be submitted for qid {qid}:\n {code}")
    if os.getenv('CONFIRM'):
        answer = input(f"n to skip solution, s to skip question, any key to submit").lower().strip()
        if answer == 's':
            return True
        if answer == 'n':
            return False
    body = {
        'lang': "cpp",
        'question_id': qid,
        'typed_code': code
    }
    response = requests.post('https://leetcode.com/problems/combinations/submit/', json=body, headers=headers)
    if response.status_code == 429:
        print("Got rate limited, sleeping for 6 seconds. Skipping solution.")
        time.sleep(6)
        return False
    submission = re.search(r'submission_id"\s*:\s*(\d+)', response.text)
    if submission is not None:
        print(f"Submission: https://leetcode.com/submissions/detail/{submission.group(1)}/")
    else:
        print(response.text)
    return True


def can_compile(code: str) -> bool:
    compiler_path = shutil.which("g++")
    if compiler_path is None:
        print("Could not find g++. Pass NOCOMPILE=1 flag to not use the sanity-check compile. Exiting.")
        exit(1)
    code = "#include <bits/stdc++.h>\nusing namespace std;\n" + code + "\nint main() { return 0; }"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp') as codefile:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.out') as outfile:
            codefile.write(code)
            codefile.flush()
            try:
                result = subprocess.run([compiler_path, codefile.name, '-o', outfile.name], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            except Exception as e:
                print(f"g++ exception: {e}")
                return False
            if result.returncode == 0:
                return True
    return False


if __name__ == '__main__':
    body = {
        "operationName": "allQuestionsStatusesRaw",
        "variables": {},
        "query": "query allQuestionsStatusesRaw {\n  allQuestions: allQuestionsRaw {\n    questionId\n   difficulty \n titleSlug \n status\n    __typename\n  }\n}\n"
    }
    difficulties = ["Easy"]
    if os.getenv('MEDIUM'):
        difficulties.append('Medium')
    questions = [q for q in
                 requests.get('https://leetcode.com/graphql', json=body, headers=headers).json()['data']['allQuestions']
                 if q['difficulty'] in difficulties and q['status'] is None]
    random.shuffle(questions)
    for q in questions:
        solve(q['titleSlug'], q['questionId'])
