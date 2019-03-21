#!/bin/sh/env python

import os
import sys

import requests

ENDPOINT = 'https://www.udemy.com/instructor-api/v1/'


def query_string(params):
    return '&'.join(f'{k}={v}' for k, v in params.items())


def param_fields(fields):
    return {f'fields[{k}]': ','.join(v) for k, v in fields.items()}


def match(terms, text):
    return terms.lower() in text.lower()


class Question:
    def __init__(self, parent, id, title):
        self.parent = parent
        self.id = id
        self.title = title
        self.replies = []


class Course:
    def __init__(self, parent, id, title):
        self.parent = parent
        self.id = id
        self.title = title
        self.questions = []

    def get_questions(self):
        params = param_fields({
            'question': ['title', 'num_replies', 'replies', 'content'],
            'answer': ['body'],
        })
        params['page_size'] = 100
        url = f'{ENDPOINT}courses/{self.id}/questions/?{query_string(params)}'
        while True:
            response = requests.get(url, headers=self.parent.headers)
            data = response.json()
            for question in data['results']:
                q = Question(self, question['id'], question['title'])
                self.questions.append(q)
                for answer in question['replies']:
                    q.replies.append(answer['body'])
            if data['next'] is None:
                break

            url = data['next']


class Udemy:
    def __init__(self):
        self.token = os.getenv('UDEMY_TOKEN')
        if not self.token:
            raise Exception('Missing token, please set environment variable: UDEMY_TOKEN')

        self.headers = {
            'authorization': f'Bearer {self.token}',
        }

        self.courses = []

    def load(self):
        self.get_courses()

        for course in u.courses:
            course.get_questions()

    def get_courses(self):
        url = f'{ENDPOINT}taught-courses/courses/?fields[course]=title,is_paid'
        response = requests.get(url, headers=self.headers)
        for course in response.json()['results']:
            if course['is_paid']:
                self.courses.append(Course(self, course['id'], course['title']))

    def search(self, terms):
        list = []
        for c in self.courses:
            for q in c.questions:
                if match(terms, q.title):
                    list.append(q)
                else:
                    for r in q.replies:
                        if match(terms, r):
                            list.append(q)
                            break
        return list


if __name__ == '__main__':
    try:
        u = Udemy()
    except Exception as e:
        print(e)
        sys.exit(1)

    print('loading...')
    u.load()

    while True:
        terms = input('Terms: ')
        if not terms.strip():
            break

        results = u.search(terms.strip())
        if results:
            for result in results:
                print(f'******* {result.title}')
                print('\n'.join(result.replies))
                print('**\n')
        else:
            print('There are no matches!')
