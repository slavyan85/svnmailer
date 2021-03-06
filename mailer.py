# coding=utf-8
__author__ = 'v.kryuchenko'


import argparse
import pysvn
import json
import smtplib
import datetime
import re
from email.mime.text import MIMEText


class Mailer:
    @staticmethod
    def __target_date(start_date, delta):
        result = start_date - datetime.timedelta(days=delta)
        return result

    def __init__(self, config):
        with open(config, 'r') as cf:
            options = json.loads(cf.read(), encoding='utf8')
        self.tracker = options['tracker']
        self.smtp_url = options['sender']['server_url']
        self.smtp_login = options['sender']['login']
        self.smtp_pass = options['sender']['password']
        self.signature = options['sender']['signature']
        self.svn_root = options['svn_root']
        self.commits = int(options['commits'])
        self.days = int(options['days'])
        self.developers = options['developers']
        self.watchers = options['watchers']
        self.stop_day = datetime.datetime.today()
        self.start_day = self.__target_date(self.stop_day, self.days)
        with open(options['sender']['template'], 'r') as tf:
            self.template = options['sender']['template'] = tf.read()

    def task_to_link(self, message):
        reg = re.compile('{}-\d*'.format(self.tracker['task_prefix']))
        reg_result = reg.findall(message)
        if reg_result:
            for match in reg_result:
                message = message.replace(match, '<a href="{tu}/{m}">{m}</a>'.format(tu=self.tracker['base_url'],
                                                                                     m=match))
        return message

    def commits_by_authors(self):
        """
        :return: dict(author=dict(revision=message))
        """
        def ssl_server_trust_prompt(trust_dict):
            return True, trust_dict['failures'], True

        result = {}
        svn = pysvn.Client()
        if self.svn_root.startswith('https'):
            svn.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
        start_revision = svn.log(self.svn_root, limit=1, discover_changed_paths=False)[0].revision.number
        end_revision = start_revision - self.commits
        draft_log = svn.log(self.svn_root,
                            revision_start=pysvn.Revision(pysvn.opt_revision_kind.number, start_revision),
                            revision_end=pysvn.Revision(pysvn.opt_revision_kind.number, end_revision))
        log = [commit for commit in draft_log if commit.author in self.developers and datetime.datetime.fromtimestamp(commit.date) > self.start_day]
        for commit in log:
            author = commit.author
            revision = str(commit.revision.number)
            message = self.task_to_link(commit.message)
            if author not in result:
                result.update({author: {revision: message}})
            else:
                result[author].update({revision: message})
        return result

    def send_email(self, target, message):
        msg_object = MIMEText(_text=message, _subtype='html', _charset='utf8')
        start_time = self.start_day.strftime('%d-%m-%y %H:%M')
        end_time = self.stop_day.strftime('%d-%m-%Y %H:%M')
        msg_object['Subject'] = 'Commits between {s} -- {e}'.format(s=start_time, e=end_time)
        msg_object['From'] = '{s} <{a}>'.format(s=self.signature, a=self.smtp_login)
        msg_object['To'] = target
        try:
            smtp = smtplib.SMTP_SSL(host=self.smtp_url)
            smtp.login(self.smtp_login, self.smtp_pass)
            smtp.sendmail(self.smtp_login, [target], msg_object.as_string())
            smtp.quit()
            smtp.close()
        except Exception as ex:
            print('SMTP error.\n{}'.format(ex))

    def render_template(self, authors, watcher):
        content_list = []
        for author in authors:
            author_commits = '<b>{}</b><br>'.format(author) if author in self.watchers[watcher] else ''
            author_commits += '<br>'.join(['{r}\t:\t{m}'.format(r=commit, m=authors[author][commit]) for commit in authors[author] if author in self.watchers[watcher]])
            content_list.append(author_commits)
        content = '<hr>'.join([content_item for content_item in content_list if content_item])
        return self.template.format(content=content)

    def run(self):
        authors = self.commits_by_authors()
        for watcher in self.watchers:
            email_body = self.render_template(authors, watcher)
            self.send_email(watcher, email_body)


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
