# coding=utf-8
__author__ = 'v.kryuchenko'


import pysvn
import json
import smtplib
import datetime
from email.mime.text import MIMEText


class Mailer:
    def __init__(self, config):
        with open(config, 'r') as cf:
            options = json.loads(cf.read(), encoding='utf8')
        self.smpt_url = options['sender']['server_url']
        self.smpt_login = options['sender']['login']
        self.smpt_pass = options['sender']['password']
        self.svn_root = options['svn_root']
        self.depth = int(options['depth'])
        self.developers = options['developers']
        self.watchers = options['watchers']
        self.today = datetime.datetime.today()
        self.yesterday = self.today.replace(day=(self.today.day - 1))

    def get_commits(self):
        svn = pysvn.Client()
        start_revision = svn.log(self.svn_root, limit=1, discover_changed_paths=False)[0].revision.number
        end_revision = start_revision - self.depth
        draft_log = svn.log(self.svn_root,
                            revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, start_revision),
                            revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, end_revision))
        commits = None

    def send_email(self, watcher):
        pass

    def run(self):
        pass


if __name__ == '__main__':
    mailer = Mailer('config.json')
    mailer.run()
