##	plugins/dialogs.py
##
## Gajim Team:
## 	- Yann Le Boulanger <asterix@lagaule.org>
## 	- Vincent Hanquez <tab@snarc.org>
##  - Nikos Kouremenos <nkour@jabber.org>
##
##	Copyright (C) 2003-2005 Gajim Team
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 2 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import gobject
import string
from common import i18n
_ = i18n._
APP = i18n.APP
gtk.glade.bindtextdomain (APP, i18n.DIR)
gtk.glade.textdomain (APP)

GTKGUI_GLADE='plugins/gtkgui/gtkgui.glade'


class infoUser_Window:
	"""Class for user's information window"""
	def on_user_information_window_destroy(self, widget=None):
		"""close window"""
		del self.plugin.windows[self.account]['infos'][self.jid]

	def on_close_button_clicked(self, widget):
		"""Save user's informations and update the roster on the Jabber server"""
		if self.vcard:
			widget.get_toplevel().destroy()
			return
		#update user.name if it's not ""
		name_entry = self.xml.get_widget('nickname_entry')
		new_name = name_entry.get_text()
		if new_name != self.user.name and new_name != '':
			self.user.name = new_name
			for i in self.plugin.roster.get_user_iter(self.user.jid, self.account):
				self.plugin.roster.tree.get_model().set_value(i, 1, new_name)
			self.plugin.send('UPDUSER', self.account, (self.user.jid, \
				self.user.name, self.user.groups))
		#log history ?
		account_info = self.plugin.accounts[self.account]
		oldlog = 1
		no_log_for = []
		if account_info.has_key('no_log_for'):
			no_log_for = account_info['no_log_for'].split()
			if self.user.jid in no_log_for:
				oldlog = 0
		log = self.xml.get_widget('log_checkbutton').get_active()
		if not log and not self.user.jid in no_log_for:
			no_log_for.append(self.user.jid)
		if log and self.user.jid in no_log_for:
			no_log_for.remove(self.user.jid)
		if oldlog != log:
			account_info['no_log_for'] = string.join(no_log_for, ' ')
			self.plugin.accounts[self.account] = account_info
			self.plugin.send('CONFIG', None, ('accounts', self.plugin.accounts, \
				'Gtkgui'))
		widget.get_toplevel().destroy()

	def set_value(self, entry_name, value):
		try:
			self.xml.get_widget(entry_name).set_text(value)
		except AttributeError, e:
			pass

	def set_values(self, vcard):
		for i in vcard.keys():
			if type(vcard[i]) == type({}):
				for j in vcard[i].keys():
					self.set_value(i+'_'+j+'_entry', vcard[i][j])
			else:
				if i == 'DESC':
					self.xml.get_widget('DESC_textview').get_buffer().\
						set_text(vcard[i], 0)
				else:
					self.set_value(i+'_entry', vcard[i])

	def fill_jabber_page(self):
		self.xml.get_widget('nickname_label').set_text(self.user.name)
		self.xml.get_widget('jid_label').set_text(self.user.jid)
		self.xml.get_widget('subscription_label').set_text(self.user.sub)
		if self.user.ask:
			self.xml.get_widget('ask_label').set_text(self.user.ask)
		else:
			self.xml.get_widget('ask_label').set_text('None')
		self.xml.get_widget('nickname_entry').set_text(self.user.name)
		account_info = self.plugin.accounts[self.account]
		log = 1
		if account_info.has_key('no_log_for'):
			if self.user.jid in account_info['no_log_for'].split(' '):
				log = 0
		self.xml.get_widget('log_checkbutton').set_active(log)
		resources = self.user.resource + ' (' + str(self.user.priority) + ')'
		if not self.user.status:
			user.status = ''
		stats = self.user.show + ' : ' + self.user.status
		for u in self.plugin.roster.contacts[self.account][self.user.jid]:
			if u.resource != self.user.resource:
				resources += '\n' + u.resource + ' (' + str(u.priority) + ')'
				if not u.status:
					u.status = ''
				stats += '\n' + u.show + ' : ' + u.status
		self.xml.get_widget('resource_label').set_text(resources)
		self.xml.get_widget('status_label').set_text(stats)
		plugin.send('ASK_VCARD', self.account, self.user.jid)

	def add_to_vcard(self, vcard, entry, txt):
		"""Add an information to the vCard dictionary"""
		entries = string.split(entry, '_')
		loc = vcard
		while len(entries) > 1:
			if not loc.has_key(entries[0]):
				loc[entries[0]] = {}
			loc = loc[entries[0]]
			del entries[0]
		loc[entries[0]] = txt
		return vcard

	def make_vcard(self):
		"""make the vCard dictionary"""
		entries = ['FN', 'NICKNAME', 'BDAY', 'EMAIL_USERID', 'URL', 'TEL_NUMBER',\
			'ADR_STREET', 'ADR_EXTADR', 'ADR_LOCALITY', 'ADR_REGION', 'ADR_PCODE',\
			'ADR_CTRY', 'ORG_ORGNAME', 'ORG_ORGUNIT', 'TITLE', 'ROLE'] 
		vcard = {}
		for e in entries: 
			txt = self.xml.get_widget(e+'_entry').get_text()
			if txt != '':
				vcard = self.add_to_vcard(vcard, e, txt)
		buffer = self.xml.get_widget('DESC_textview').get_buffer()
		start_iter = buffer.get_start_iter()
		end_iter = buffer.get_end_iter()
		txt = buffer.get_text(start_iter, end_iter, 0)
		if txt != '':
			vcard['DESC'] = txt
		return vcard

	def on_publish_button_clicked(self, widget):
		if not self.plugin.connected[self.account]:
			warning_dialog(_("You must be connected to publish your informations"))
			return
		vcard = self.make_vcard()
		nick = ''
		if vcard.has_key('NICKNAME'):
			nick = vcard['NICKNAME']
		if nick == '':
			nick = self.plugin.accounts[self.account]['name']
		self.plugin.nicks[self.account] = nick
		self.plugin.send('VCARD', self.account, vcard)

	def on_retrieve_button_clicked(self, widget):
		if self.plugin.connected[self.account]:
			self.plugin.send('ASK_VCARD', self.account, self.jid)
		else:
			warning_dialog(_('You must be connected to get your informations'))

	def change_to_vcard(self):
		self.xml.get_widget('information_notebook').remove_page(0)
		self.xml.get_widget('nickname_label').set_text('Personal details')
		information_hbuttonbox = self.xml.get_widget('information_hbuttonbox')
		#publish button
		button = gtk.Button(stock=gtk.STOCK_GOTO_TOP)
		button.get_children()[0].get_children()[0].get_children()[1].\
			set_text('Publish')
		button.connect('clicked', self.on_publish_button_clicked)
		button.show_all()
		information_hbuttonbox.pack_start(button)
		#retrieve button
		button = gtk.Button(stock=gtk.STOCK_GOTO_BOTTOM)
		button.get_children()[0].get_children()[0].get_children()[1].\
			set_text('Retrieve')
		button.connect('clicked', self.on_retrieve_button_clicked)
		button.show_all()
		information_hbuttonbox.pack_start(button)
		#close button at the end
		button = self.xml.get_widget('close_button')
		information_hbuttonbox.reorder_child(button, 2)

	#the user variable is the jid if vcard is true
	def __init__(self, user, plugin, account, vcard=False):
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'vcard_information_window', APP)
		self.window = self.xml.get_widget('vcard_information_window')
		self.plugin = plugin
		self.user = user #don't use it is vcard is true
		self.account = account
		self.vcard = vcard

		if vcard:
			self.jid = user
			self.change_to_vcard()
		else:
			self.jid = user.jid
			self.fill_jabber_page()

		self.xml.signal_autoconnect(self)

class passphrase_Window:
	"""Class for Passphrase Window"""
	def run(self):
		"""Wait for Ok button to be pressed and return passphrase"""
		rep = self.win.run()
		if rep == gtk.RESPONSE_OK:
			msg = self.entry.get_text()
		else:
			msg = -1
		chk = self.xml.get_widget("save_checkbutton")
		self.win.destroy()
		return msg, chk.get_active()

	def on_key_pressed(self, widget, event):
		if event.keyval == gtk.keysyms.Return:
			if self.autoconnect:
				self.on_ok_clicked(widget)
			else:
				self.win.response(gtk.RESPONSE_OK)

	def on_ok_clicked(self, widget):
		if self.autoconnect:
			self.msg = self.entry.get_text()
			gtk.main_quit()
	
	def on_cancel_clicked(self, widget):
		if self.autoconnect:
			gtk.main_quit()
	
	def get_pass(self):
		self.autoconnect = 0
		chk = self.xml.get_widget("save_checkbutton")
		self.win.destroy()
		return self.msg, chk.get_active()
		
	def delete_event(self, widget=None):
		"""close window"""
		if self.autoconnect:
			gtk.main_quit()

	def __init__(self, txt, autoconnect=0):
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'Passphrase', APP)
		self.win = self.xml.get_widget("Passphrase")
		self.entry = self.xml.get_widget("entry")
		self.msg = -1
		self.autoconnect = autoconnect
		self.xml.get_widget("label").set_text(txt)
		self.xml.signal_connect('gtk_widget_destroy', self.delete_event)
		self.xml.signal_connect('on_ok_clicked', self.on_ok_clicked)
		self.xml.signal_connect('on_cancel_clicked', self.on_cancel_clicked)
		self.xml.signal_connect('on_Passphrase_key_press_event', \
			self.on_key_pressed)

class choose_gpg_Window:
	"""Class for Away Message Window"""
	def run(self):
		"""Wait for Ok button to be pressed and return the selected key"""
		rep = self.xml.get_widget("Choose_gpg_key").run()
		if rep == gtk.RESPONSE_OK:
			selection = self.treeview.get_selection()
			(model, iter) = selection.get_selected()
			keyID = [model.get_value(iter, 0), model.get_value(iter, 1)]
		else:
			keyID = -1
		self.xml.get_widget("Choose_gpg_key").destroy()
		return keyID

	def fill_tree(self, list):
		model = self.treeview.get_model()
		for keyID in list.keys():
			model.append((keyID, list[keyID]))
	
	def __init__(self):
		#list : {keyID: userName, ...}
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'Choose_gpg_key', APP)
		self.window = self.xml.get_widget("Choose_gpg_key")
		self.treeview = self.xml.get_widget("treeview")
		model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.treeview.set_model(model)
		#columns
		renderer = gtk.CellRendererText()
		self.treeview.insert_column_with_attributes(-1, _('KeyID'), renderer, \
			text=0)
		renderer = gtk.CellRendererText()
		self.treeview.insert_column_with_attributes(-1, _('User name'), renderer,\
			text=1)

class awayMsg_Window:
	"""Class for Away Message Window"""
	def run(self):
		"""Wait for Ok button to be pressed and return away messsage"""
		rep = self.xml.get_widget("Away_msg").run()
		if rep == gtk.RESPONSE_OK:
			beg, end = self.txtBuffer.get_bounds()
			msg = self.txtBuffer.get_text(beg, end, 0)
			self.plugin.config['last_msg'] = msg
		else:
			msg = -1
		self.xml.get_widget("Away_msg").destroy()
		return msg

	def on_entry_changed(self, widget, data=None):
		model = widget.get_model()
		active = widget.get_active()
		if active < 0:
			return None
		name = model[active][0]
		self.txtBuffer.set_text(self.values[name])
	
	def on_key_pressed(self, widget, event):
		if event.keyval == gtk.keysyms.Return:
			if (event.state & gtk.gdk.CONTROL_MASK):
				self.xml.get_widget("Away_msg").response(gtk.RESPONSE_OK)
	
	def __init__(self, plugin):
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'Away_msg', APP)
		self.plugin = plugin
		txt = self.xml.get_widget("textview")
		self.txtBuffer = txt.get_buffer()
		self.txtBuffer.set_text(self.plugin.config['last_msg'])
		self.values = {'':''}
		i = 0
		while self.plugin.config.has_key('msg%s_name' % i):
			self.values[self.plugin.config['msg%s_name' % i]] = \
				self.plugin.config['msg%s' % i]
			i += 1
		liststore = gtk.ListStore(str, str)
		cb = self.xml.get_widget('comboboxentry')
		cb.set_model(liststore)
		cb.set_text_column(0)
		for val in self.values.keys():
			cb.append_text(val)
		self.xml.signal_connect('on_comboboxentry_changed', self.on_entry_changed)
		self.xml.signal_connect('on_key_press_event', self.on_key_pressed)

class add_contact_window:
	"""Class for add_contact_window"""
	def on_cancel_button_clicked(self, widget):
		"""When Cancel button is clicked"""
		widget.get_toplevel().destroy()

	def on_subscribe_button_clicked(self, widget):
		"""When Subscribe button is clicked"""
		jid = self.xml.get_widget('jid_entry').get_text()
		nickname = self.xml.get_widget('nickname_entry').get_text()
		if not jid:
			return
		if jid.find('@') < 0:
			warning_dialog(_("The contact's name must be something like login@hostname"))
			return
		message_buffer = self.xml.get_widget('message_textview').get_buffer()
		start_iter = message_buffer.get_start_iter()
		end_iter = message_buffer.get_end_iter()
		message = message_buffer.get_text(start_iter, end_iter, 0)
		self.plugin.roster.req_sub(self, jid, message, self.account, nickname)
		if self.xml.get_widget('auto_authorize_checkbutton').get_active():
			self.plugin.send('AUTH', self.account, jid)
		widget.get_toplevel().destroy()
		
	def fill_jid(self):
		agent_combobox = self.xml.get_widget('agent_combobox')
		model = agent_combobox.get_model()
		index = agent_combobox.get_active()
		jid = self.xml.get_widget('uid_entry').get_text()
		if index > 0:
			jid = jid.replace('@', '%')
		agent = model[index][1]
		if agent:
			jid += '@' + agent
		self.xml.get_widget('jid_entry').set_text(jid)

	def on_agent_combobox_changed(self, widget):
		self.fill_jid()

	def guess_agent(self):
		uid = self.xml.get_widget('uid_entry').get_text()
		agent_combobox = self.xml.get_widget('agent_combobox')
		model = agent_combobox.get_model()
		
		#If login contains only numbers, it's probably an ICQ number
		try:
			string.atoi(uid)
		except:
			pass
		else:
			if 'ICQ' in self.agents:
				agent_combobox.set_active(self.agents.index('ICQ'))
				return
		agent_combobox.set_active(0)

	def set_nickname(self):
		uid = self.xml.get_widget('uid_entry').get_text()
		nickname = self.xml.get_widget('nickname_entry').get_text()
		if nickname == self.old_uid_value:
			self.xml.get_widget('nickname_entry').set_text(uid.split('@')[0])
			
	def on_uid_entry_changed(self, widget):
		self.guess_agent()
		self.set_nickname()
		self.fill_jid()
		uid = self.xml.get_widget('uid_entry').get_text()
		self.old_uid_value = uid.split('@')[0]
		
	def __init__(self, plugin, account, jid=None):
		if not plugin.connected[account]:
			warning_dialog(_('You must be connected to add a contact'))
			return
		self.plugin = plugin
		self.account = account
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'add_contact_window', APP)
		self.window = self.xml.get_widget('add_contact_window')
		self.old_uid_value = ''
		liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
		liststore.append(['Jabber', ''])
		self.agents = ['Jabber']
		jid_agents = []
		for j in self.plugin.roster.contacts[account]:
			user = self.plugin.roster.contacts[account][j][0]
			if 'Agents' in user.groups:
				jid_agents.append(j)
		for a in jid_agents:
			if a.find('aim') > -1:
				name = 'AIM'
			elif a.find('icq') > -1:
				name = 'ICQ'
			elif a.find('msn') > -1:
				name = 'MSN'
			elif a.find('yahoo') > -1:
				name = 'Yahoo!'
			else:
				name = a
			iter = liststore.append([name, a])
			self.agents.append(name)
		agent_combobox = self.xml.get_widget('agent_combobox')
		agent_combobox.set_model(liststore)
		agent_combobox.set_active(0)
		self.fill_jid()
		if jid:
			self.xml.get_widget('jid_entry').set_text(jid)
			jid_splited = jid.split('@')
			self.xml.get_widget('entry_login').set_text(jid_splited[0])
			if jid_splited[1] in jid_agents:
				agent_combobox.set_active(jid_agents.index(jid_splited[1])+1)
		self.xml.signal_autoconnect(self)

class about_Window: #FIXME: (nk) pygtk2.6 has a built-in window for that
	"""Class for about window"""
	def delete_event(self, widget):
		"""close window"""
		del self.plugin.windows['about']
		
	def on_close(self, widget):
		"""When Close button is clicked"""
		widget.get_toplevel().destroy()

	def __init__(self, plugin):
		xml = gtk.glade.XML(GTKGUI_GLADE, 'about_window', APP)
		self.window = xml.get_widget('about_window')
		self.plugin = plugin
		xml.signal_connect('gtk_widget_destroy', self.delete_event)
		xml.signal_connect('on_close_clicked', self.on_close)


class confirm_dialog:
	"""Class for confirmation dialog"""
	def get_response(self):
		response = self.dialog.run()
		self.dialog.destroy()
		return response

	def __init__(self, label):
		self.dialog = gtk.MessageDialog(None,\
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
			gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, label)

class warning_dialog:
	"""Class for warning dialog"""
	def __init__(self, label):
		self.dialog = gtk.MessageDialog(None,\
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
			gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, label)

		response = self.dialog.run()
		self.dialog.destroy()

class subscription_request_Window:
	"""Class for authorization window :
	window that appears when a user wants to add us to his/her roster"""
	def on_close_button_clicked(self, widget):
		"""When Close button is clicked"""
		widget.get_toplevel().destroy()
		
	def on_authorize_button_clicked(self, widget):
		"""Accept the request"""
		self.plugin.send('AUTH', self.account, self.jid)
		widget.get_toplevel().destroy()
		if not self.plugin.roster.contacts[self.account].has_key(self.jid):
			addContact_Window(self.plugin, self.account, self.jid)
	
	def on_deny_button_clicked(self, widget):
		"""refuse the request"""
		self.plugin.send('DENY', self.account, self.jid)
		widget.get_toplevel().destroy()
	
	def __init__(self, plugin, jid, text, account):
		xml = gtk.glade.XML(GTKGUI_GLADE, 'subscription_request_window', APP)
		self.plugin = plugin
		self.jid = jid
		self.account = account
		xml.get_widget('from_label').set_text(\
			_('Subscription request from %s') % self.jid)
		xml.get_widget('message_textview').get_buffer().set_text(text)
		xml.signal_autoconnect(self)

class join_gc:
	def delete_event(self, widget):
		"""close window"""
		del self.plugin.windows['join_gc']

	def on_close(self, widget):
		"""When Cancel button is clicked"""
		widget.get_toplevel().destroy()

	def on_join(self, widget):
		"""When Join button is clicked"""
		nick = self.xml.get_widget('entry_nick').get_text()
		room = self.xml.get_widget('entry_room').get_text()
		server = self.xml.get_widget('entry_server').get_text()
		passw = self.xml.get_widget('entry_pass').get_text()
		jid = '%s@%s' % (room, server)
		self.plugin.windows[self.account]['gc'][jid] = gtkgui.gc(jid, nick, \
			self.plugin, self.account)
		#TODO: verify entries
		self.plugin.send('GC_JOIN', self.account, (nick, room, server, passw))
		widget.get_toplevel().destroy()

	def __init__(self, plugin, account, server='', room = ''):
		if not plugin.connected[account]:
			warning_dialog(_("You must be connected to join a group chat on this serveur"))
			return
		self.plugin = plugin
		self.account = account
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'Join_gc', APP)
		self.window = self.xml.get_widget('Join_gc')
		self.xml.get_widget('entry_server').set_text(server)
		self.xml.get_widget('entry_room').set_text(room)
		self.xml.get_widget('entry_nick').set_text(self.plugin.nicks[self.account])
		self.xml.signal_connect('gtk_widget_destroy', self.delete_event)
		self.xml.signal_connect('on_cancel_clicked', self.on_close)
		self.xml.signal_connect('on_join_clicked', self.on_join)

class new_message_window: #FIXME: NOT READY
	def delete_event(self, widget):
		"""close window"""
		del self.plugin.windows['join_gc']

	def on_close(self, widget):
		"""When Cancel button is clicked"""
		widget.get_toplevel().destroy()

	def on_join(self, widget):
		"""When Join button is clicked"""
		nick = self.xml.get_widget('entry_nick').get_text()
		room = self.xml.get_widget('entry_room').get_text()
		server = self.xml.get_widget('entry_server').get_text()
		passw = self.xml.get_widget('entry_pass').get_text()
		jid = '%s@%s' % (room, server)
		self.plugin.windows[self.account]['gc'][jid] = gtkgui.gc(jid, nick, \
			self.plugin, self.account)
		#TODO: verify entries
		self.plugin.send('GC_JOIN', self.account, (nick, room, server, passw))
		widget.get_toplevel().destroy()

	def __init__(self, plugin, account, server='', room = ''):
		#FIXME:
		return True
		
		if not plugin.connected[account]:
			warning_dialog(_("You must be connected to join a group chat on this serveur"))
			return
		self.plugin = plugin
		self.account = account
		self.xml = gtk.glade.XML(GTKGUI_GLADE, 'Join_gc', APP)
		self.window = self.xml.get_widget('Join_gc')
		self.xml.get_widget('entry_server').set_text(server)
		self.xml.get_widget('entry_room').set_text(room)
		self.xml.get_widget('entry_nick').set_text(self.plugin.nicks[self.account])
		self.xml.signal_connect('gtk_widget_destroy', self.delete_event)
		self.xml.signal_connect('on_cancel_clicked', self.on_close)
		self.xml.signal_connect('on_join_clicked', self.on_join)
