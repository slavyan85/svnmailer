# coding=utf-8
__author__ = 'v.kryuchenko'


import argparse
import pysvn
import json
import smtplib
import datetime
from email.mime.text import MIMEText


class Mailer:
    def __init__(self, config):
        with open(config, 'r') as cf:
            options = json.loads(cf.read(), encoding='utf8')
        self.tracker = options['tracker']
        self.smpt_url = options['sender']['server_url']
        self.smpt_login = options['sender']['login']
        self.smpt_pass = options['sender']['password']
        self.svn_root = options['svn_root']
        self.depth = int(options['depth'])
        self.developers = options['developers']
        self.watchers = options['watchers']
        today = datetime.datetime.today()
        self.yesterday = today.replace(day=(today.day - 1))

    def commits_by_authors(self):
        """
        :return: dict(author=dict(revision=message))
        """
        result = {}
        svn = pysvn.Client()
        start_revision = svn.log(self.svn_root, limit=1, discover_changed_paths=False)[0].revision.number
        end_revision = start_revision - self.depth
        draft_log = svn.log(self.svn_root,
                            revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, start_revision),
                            revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, end_revision))
        log = [commit for commit in draft_log if commit.author in self.developers and datetime.datetime.fromtimestamp(commit.date) > self.yesterday]
        for commit in log:
            print()
            author = commit.author
            revision = commit.revision.number
            message = commit.message
            if author not in result:
                result.update({author: {revision: message}})
            else:
                result[author].update({revision: message})
        return result

    def send_email(self, watcher):
        pass

    def run(self):
        authors = self.commits_by_authors()
        for author in authors:
            print(author)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        action='store',
                        dest='config_file',
                        default='config.json',
                        help='Path to configuration file. Default <config.json>')
    opts = parser.parse_args()

    mailer = Mailer(opts.config_file)
    mailer.run()
