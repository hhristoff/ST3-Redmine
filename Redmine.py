import json
import urllib.request

import sublime
import sublime_plugin


class RedmineManager():
    def __init__(self):
        self.settings = {}
        settings = sublime.load_settings('Redmine.sublime-settings')
        self.settings['username'] = settings.get('username')
        self.settings['password'] = settings.get('password')
        self.settings['redmine_url'] = settings.get('redmine_url')
        self.settings['redmine_user_id'] = settings.get('redmine_user_id')

    def list_stuff_to_do(self):
        request = urllib.request.Request(self.settings['redmine_url'] +
                                         "/issues.json?assigned_to_id=" +
                                         self.settings["redmine_user_id"])
        auth_handler = urllib.request.HTTPBasicAuthHandler()
        auth_handler.add_password("Redmine API",
                                  self.settings["redmine_url"],
                                  self.settings["username"],
                                  self.settings["password"])
        opener = urllib.request.build_opener(auth_handler)
        urllib.request.install_opener(opener)
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode())
        issues = data["issues"]
        return issues


class StuffToDoCommand(sublime_plugin.WindowCommand):
    def __init__(self, *a, **ka):
        super(StuffToDoCommand, self).__init__(*a, **ka)
        self.issues = None
        self.issue_names = []

    def on_done(self, picked):
        if picked == -1:
            return
        issue = self.issues[picked]
        url = self.manager.settings['redmine_url'] + "/issues/" + str(issue["id"])
        self.window.run_command('open_url', {'url': url})

    def async_load(self):
        self.issue_names = []
        self.issues = self.manager.list_stuff_to_do()
        for issue in self.issues:
            issue_entry = []
            issue_entry.append("#"+str(issue["id"])+" "+issue["project"]["name"] +": "+ issue["subject"] + " (" + str(issue["done_ratio"]) + "%)")
            issue_entry.append(issue["tracker"]["name"] +" / "+ issue["status"]["name"] + " / " + issue["priority"]["name"])
            issue_entry.append("Author: "+issue["author"]["name"])
            issue_entry.append(issue["description"][0:85])
            if "due_date" in issue:
                issue_entry.append("From: "+issue["start_date"] +" To: "+ issue["due_date"])
            else:
                issue_entry.append("From: "+issue["start_date"])
            if "estimated_hours" in issue:
                issue_entry.append("Estimated Hours: "+str(issue["estimated_hours"]))
            self.issue_names.append(issue_entry)
        self.window.show_quick_panel(self.issue_names, self.on_done)

    def run(self):
        self.manager = RedmineManager()
        sublime.set_timeout_async(self.async_load, 0)
