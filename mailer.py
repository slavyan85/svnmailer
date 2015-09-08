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
        self.smtp_url = options['sender']['server_url']
        self.smtp_login = options['sender']['login']
        self.smtp_pass = options['sender']['password']
        self.signature = options['signature']
        self.svn_root = options['svn_root']
        self.depth = int(options['depth'])
        self.developers = options['developers']
        self.watchers = options['watchers']
        today = datetime.datetime.today()
        self.yesterday = today.replace(day=(today.day - 1))
        with open(options['sender']['template'], 'r') as tf:
            self.template = options['sender']['template'] = tf.read()

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
            author = commit.author
            revision = commit.revision.number
            message = commit.message
            if author not in result:
                result.update({author: {revision: message}})
            else:
                result[author].update({revision: message})
        return result

    def send_email(self, target, message):
        msg_object = MIMEText(_text=message, _subtype='html', _charset='utf8')
        msg_object['Subject'] = 'Commits at {}'.format(str(self.yesterday))
        msg_object['From'] = '{s} <{a}>'.format(s=self.signature, a=self.smtp_login)
        msg_object['To'] = target
        try:
            smtp = smtplib.SMTP_SSL(host=self.smtp_url)
            smtp.login(self.smtp_login, self.smtp_pass)
            smtp.sendmail(self.smtp_login, [target], msg_object)
        except Exception as ex:
            print('SMTP error.\n{}'.format(ex))

    def run(self):
        content_list = []
        authors = self.commits_by_authors()
        for author in authors:
            author_commits = '<br>'.join(['{r}\t:\t{m}'.format(r=commit['revision'], m=commit['message']) for commit in authors[author]])
            content_list.append(author_commits)
        content = '<hr>'.join(content_list)
        print(self.template.format(content=content))



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
