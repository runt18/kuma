from __future__ import with_statement

import json
import os
import urllib

from django.conf import settings


GITHUB_REPOS = "https://api.github.com/repos/mozilla/kuma/contributors"


class Human(object):
    def __init__(self):
        self.name = None
        self.website = None


class HumansTXT(object):

    def generate_file(self):
        githubbers = self.get_github(json.load(urllib.urlopen(GITHUB_REPOS)))
        path = os.path.join(settings.HUMANSTXT_ROOT, "humans.txt")

        with open(path, 'w') as target:
            self.write_to_file(githubbers, target,
                               "Contributors on GitHub", "Developer")

    def write_to_file(self, humans, target, message, role):
        target.write("{0!s} \n".format(message))
        for h in humans:
            target.write("{0!s}: {1!s} \n".format(role, h.name.encode('ascii', 'ignore')))
            if h.website is not None:
                target.write("Website: {0!s} \n".format(h.website))
                target.write('\n')
        target.write('\n')

    def get_github(self, data=None):
        if not data:
            raw_data = json.load(urllib.urlopen(GITHUB_REPOS))
        else:
            raw_data = data

        humans = []
        for contributor in raw_data:
            human = Human()
            human.name = contributor.get('name', contributor['login'])
            human.website = contributor.get('blog', None)
            humans.append(human)

        return humans

    def split_name(self, name):
        if '@' in name:
            name = name.split('@')[0]

        return name
