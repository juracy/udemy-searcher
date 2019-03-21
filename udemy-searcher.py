#!/bin/sh/env python

import os
import sys

import requests

INSTRUCTOR_ENDPOINT = 'https://www.udemy.com/instructor-api/v1/'
USER_ENDPOINT = 'https://www.udemy.com/api-2.0/users/me/'
UDEMY_QUESTIONS = 'https://www.udemy.com/{}/learn/v4/questions/'


def query_string(params):
    return '&'.join(f'{k}={v}' for k, v in params.items())


def param_fields(fields):
    return {f'fields[{k}]': ','.join(v) for k, v in fields.items()}


def match(terms, text):
    return terms.lower() in text.lower()


class Discussion:
    def __init__(self, parent, id, title, body, course):
        self.parent = parent
        self.id = id
        self.title = title
        self.body = body
        self.course = course.replace('/', '')
        self.replies = []

    def match(self, terms):
        return match(terms, self.title) or \
               match(terms, self.body) or \
               any(match(terms, r) for r in self.replies)


class Udemy:
    def __init__(self):
        self.token = os.getenv('UDEMY_TOKEN')
        if not self.token:
            raise Exception('Missing token, please set environment variable: UDEMY_TOKEN')

        self.headers = {
            'authorization': f'Bearer {self.token}',
        }

        self.courses = []
        self.discussions = []

    def get_discussions(self):
        params = param_fields({
            'course_discussion': ['id', 'title', 'body', 'replies', 'course'],
            'course_discussion_reply': ['body'],
            'course': ['url'],
        })
        params['page_size'] = 100
        url = f'{USER_ENDPOINT}searchable-taught-courses-discussions/?{query_string(params)}'
        while True:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            for discussion in data['results']:
                q = Discussion(
                    self,
                    discussion['id'],
                    discussion['title'],
                    discussion['body'],
                    discussion['course']['url'])
                q.replies = [reply['body'] for reply in discussion['replies']]
                self.discussions.append(q)
            if data['next'] is None:
                break

            url = data['next']

    def search(self, terms):
        return [q for q in self.discussions if q.match(terms)]


if __name__ == '__main__':
    try:
        u = Udemy()
    except Exception as e:
        print(e)
        sys.exit(1)

    print('loading...')
    u.get_discussions()
    print(f'{len(u.discussions)} discussions loaded')

    while True:
        terms = input('Terms: ')
        if not terms.strip():
            break

        results = u.search(terms.strip())
        if results:
            for result in results:
                print(f'******* {result.title}')
                print(f'URL: {UDEMY_QUESTIONS.format(result.course)}{result.id}/')
                print(result.body)
                print('----')
                print('\n'.join(result.replies))
                print('**\n')
        else:
            print('There are no matches!')
