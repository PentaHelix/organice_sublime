import sublime, sublime_plugin, json, os, socket, re

def plugin_loaded():
	global settings
	settings = sublime.load_settings('organice.sublime-settings')
	updateSettings()

	s.connect((settings.get('on_server_ip'), 5423))

def updateSettings():
	#create settings object because sublime is fucking stupid like that and can't just read it itself
	viewSet = sublime.active_window().active_view().settings()
	setArray = ["on_server_ip", "on_filter_tags"]
	for setting in setArray:
		if viewSet.has(str(setting)):
			settings.set(setting, viewSet.get(str(setting)))


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
q = []
settings = None
projFile = ""

class ListTodoCommand(sublime_plugin.WindowCommand):

	def run(self):
		global q
		tasks = self.GetTasks()
		q = [["New task", "Add a new task to your list..."]]
		for task in tasks:
			if(task['done']):
				q.append(["[X] "+task['text'], "#"+str(task['id'])+": " + ", ".join(task['tags'])])
			else: 
				q.append(["[  ] "+task['text'], "#"+str(task['id'])+": " + ", ".join(task['tags'])])
		
		self.window.show_quick_panel(q, self.SelectedLine, 0, 0, self.HighlightedTask)

	def SelectedLine(self, i):
		if i == -1:
			return
		elif i == 0:
			self.window.show_input_panel("Task", "", self.AddedTask, None, None)
			return
		else:
			tId = int(q[i][1].split(":")[0][1:])
			self.TickTask(tId)

	def AddedTask(self, str):
		#Remove tags and links from string (via regex)
		text = re.sub(r'@\S+', "", re.sub(r'#\S+', "", str))
		text = text.strip();

		tagstr = ""
		tags = re.findall(r'\#\w+', str)
		tags = [tag.strip("#") for tag in tags]
		tagstr = ",".join(tags)
		link = re.findall(r'@\S+', str)
		if link != []:
			link = link[0][1:]

		command = "add " + text
		if tags != []:
			command += ":"+tagstr

		if link != []:
			command += ":"+link

		command += ";"

		s.send(command.encode())

	def HighlightedTask(self, i):
		pass


	def GetTasks(self):
		global settings
		s.send(("get " + ",".join(settings.get("on_filter_tags")) + ";").encode())
		i = int(s.recv(1).decode())
		i = int(s.recv(i).decode())
		js = s.recv(i).decode()
		return json.loads(js)

	def TickTask(self, i):
		print(i)
		s.send(('set ' + str(i)+';').encode());

	def WriteTasks(self, t):
		with open(sublime.installed_packages_path()+"\\..\\Packages\\Organice\\list.td", "r+") as f:
			f.truncate();
			for line in t:
				f.write("%s\r" % line)


class OpenNotesCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.open_file("notes.nt")

class Reconnect(sublime_plugin.TextCommand):
	def run(self, edit):
		global s
		global settings
		s.close();
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((settings.get('on_server_ip'), 5423))


class EventListener(sublime_plugin.EventListener):  
	def on_activated(self, view):  
		global projFile
		print(sublime.active_window().project_file_name())
		if sublime.active_window().project_file_name() != projFile:
			projFile = sublime.active_window().project_file_name()
			updateSettings()