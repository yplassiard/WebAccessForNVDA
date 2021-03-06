# globalPlugins/webAccess/widgets/genericTable.py
# -*- coding: utf-8 -*-

# This file is part of Web Access for NVDA.
# Copyright (C) 2015-2018 Accessolutions (http://accessolutions.fr)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# See the file COPYING.txt at the root of this distribution for more details.

"""Generic Table is a simple widgets which aims to represent and navigate into
an HTML table.

Sub tables are currently not supported.
"""

__version__ = "2016.11.18"

__author__ = "Yannick Plassiard <yan@mistigri.org>"


import api
import controlTypes
from NVDAObjects import NVDAObject, IAccessible
import ui

from globalPlugins.webAccess.webAppLib import html
from . import WebAppWidget 


class ColumnHeader(object):
	"""
	Represents a column header indicating the column's title, width and several other attributes such as if the column is part of a multi-select group,
	if it is sortable, and so on.
	WARNING: When inheriting from ColumnHeader, the title has to be non-empty as it is used to compute a unique table identifier
	which will be used to store user preferences into the main Ini file.
	"""
	
	title = None
	width = 10
	index = None
	viewPosition = None
	isSortable = False
	
	def __iint__(self, title, width, index, viewPosition=index, id=None):
		self.title = title
		if id is not None:
			self.id = id
		else:
			if title == "":
				self.id = str(index)
			else:
				self.id = title
		self.width = width
		self.index = index
		self.viewPosition = viewPosition

	def __repr__(self):
		return "%s, index %d, width %d" %(self.title, self.index, self.width)
		
	
	def sort(self):
		raise NotImplementedError("You must implement the Sort method")
	

	
class Cell(object):
	"""
	Represents a table cell with its associated content.
	"""
	colHeader = None
	name = ""
	role = controlTypes.ROLE_UNKNOWN
	value = ""
	selected = False
	checked = None
	unavailable = False
	curCharacterIndex = 0
	
	def __init__(self, colHeader, name, value=None, role=controlTypes.ROLE_UNKNOWN, checked=None, selected=False, unavailable=False, visited=False):
		if name is None:
			raise ValueError("The cell name must not be None")
		if colHeader is None:
			raise ValueError("The cell must have a column header")
		self.colHeader = colHeader
		self.name = name
		self.value = value
		self.role = role
		self.checked = checked
		self.selected = selected
		self.unavailable = unavailable
		self.visited = visited


	def speak(self, speakTitle=True):
		self.curCharacterIndex = 0
		if self.colHeader is None:
			raise ValueError("Cell not attached to a column header")
		if speakTitle and self.colHeader.title is not None and self.colHeader.title != "":
			speech.speakMessage (self.colHeader.title)
		if self.role not in [controlTypes.ROLE_LABEL, controlTypes.ROLE_STATICTEXT, controlTypes.ROLE_TABLECELL]:
			role = controlTypes.roleLabels[self.role]
		else:
			role = ""
		if self.checked is True:
			checked = u"coché"
		elif self.checked is False:
			checked = u"non coché"
		else:
			checked = ""
		if self.unavailable:
			unavailable = u"non disponible"
		else:
			unavailable = ""
		if self.selected is True:
			selected = u"sélectionné"
		else:
			selected = ""
		if self.visited:
			visited = u"Visité"
		else:
			visited= ""
		if self.value is None:
			self.value = ""
		speech.speakMessage ("%s %s %s %s %s %s %s" % (self.name, role, self.value, checked, unavailable, selected, visited))
		
	def brlText(self):
		"""
		This returns a text to be written to a braille display.
		"""
		if self.role == controlTypes.ROLE_RADIOBUTTON:
			if self.unavailable:
				name = ""
			elif self.checked:
				name = "(x)"
			else:
				name = "( )"
		elif self.role == controlTypes.ROLE_CHECKBOX:
			if self.checked:
				name = "[x]"
			else:
				name = "[ ]"
		else:
			name = self.name
		s = name
		if self.value is not None:
			s += " " + self.value
			s = s.strip()
		s = s.replace ("/", ".")
		s = s + "                                   "
		return s[0:self.colHeader.width]
	
	def updatePosition(self):
		pass

	def setFocus(self):
		api.setNavigatorObject(self.obj)
		self.obj.setFocus()
	
	def getText(self):
		s = self.name + " " + self.value
		return s.strip ()
	
	def nextCharacter(self):
		t = self.getText()
		if self.curCharacterIndex >= len(t)-1:
			speech.speakMessage (u"fin")
		else:
			self.curCharacterIndex += 1
		if len(t) > 0:
			speech.speakMessage (t[self.curCharacterIndex])

		
	def priorCharacter(self):
		t = self.getText()
		if self.curCharacterIndex <= 0:
			speech.speakMessage(u"début")
		else:
			self.curCharacterIndex -= 1
		if len(t) > 0:
			speech.speakMessage(t[self.curCharacterIndex])
				
class Row(object):
	"""
	Represents a table row, containing one or more Cell object.
	"""
	_cells = []
	
	def getCell(self, numCol):
		if numCol < 1 or numCol > len(self._cells):
			return None
		else:
			return self._cells[numCol-1]
	
	def getCells(self):
		return self._cells
class GenericTable(WebAppWidget):
	identifier = ""
	_selectedCols = []
	_colCount = 0
	_rowCount = 0
	_curRow = 1
	_curCol = 1
	brlPositions = []
	curBrlWindow = 0
	forceBrlWindow = False
	pageTitle = ""
	_colHeadersCustomized = False
	tableIniFile = None
	tableConfig = None
	userIniFile = os.path.join(globalVars.appArgs.configPath, "tableConfig.ini")
	userConfig = None
	webApp = None
	editColWidthMode = False

	def __init__(self, webApp, obj=None, tableIniFile=None, userIniFi;e=None):
		super(GenericTable, self).__init__(webApp, obj)
		self.addGestures(self.__widgetGestures)
		letters = {}
		if self.supportSearch:
			for x in range(ord('A'), ord('Z') + 1) + range(ord('a'), ord('z') + 1) + [ord(' ')]:
				c = chr(x)
				if c.isupper():
					g = "shift+" + c
				elif c == ' ':
					g = "space"
				else:
					g = c
			letters["kb:" + g] = "typeLetter"
		self.addGestures(letters)
		self.webApp = webApp
		self.pageTitle = webApp.pageTitle
		try:
			self.tableConfig = ConfigObj(self.tableIniFile, encoding="utf8")
			self.userConfig = ConfigObj(self.userIniFile, encoding="utf8")
		except:
			log.warning("Table configuration not loaded.")

	def isInTable(self):
		raise NotImplementedError

	def getTitle(self):
		return ""
	
	def getTableIdentifier(self):
		if self.identifier == "":
			self.identifier = "_".join(x.colHeader.title for x in self._row.getCells())
		return self.identifier
	
	def analyzeTitlesCol(self):
		raise NotImplementedError
	
	def customizeColHeaders(self):
		if self._colHeadersCustomized:
			return
		for ch in self._titlesCol:
			key = "width_%s" % ch.id
			w = self.getTableConfig (key)
			if w is not None: 
				ch.width = int(w)
		self._colHeadersCustomized = True
			
	def increaseColWidth(self):
		c = self.getCell()
		c.colHeader.width += 1
		speech.speakMessage (u"largeur %d" % c.colHeader.width)
		key = "width_%s" % c.colHeader.id
		self.setTableConfig (key, c.colHeader.width)
		self.displayBraille()
		
	
	def decreaseColWidth(self):
		c = self.getCell()
		if c.colHeader.width <= 1:
			speech.speakMessage (u"Largeur minimale")
			return 
		c.colHeader.width -= 1
		speech.speakMessage (u"largeur %d" % c.colHeader.width)
		key = "width_%s" % c.colHeader.id
		self.setTableConfig (key, c.colHeader.width)
		self.displayBraille()
		
	def getColCount(self):
		return self._colCount
	
	def getRowCount(self):
		return self._rowCount
	
	def getRow(self):
		raise NotImplementedError

	def getCell(self, numCol=None):
		if numCol is None:
			numCol = self._curCol
		return self.getRow().getCell(numCol)
	
	def speakCell(self, speakTitle=True):
		self.customizeColHeaders()
		cell = self.getCell()
		if cell is None:
			speech.speakMessage("erreur")
			return
		ch = cell.colHeader
		keyTitle = "title_%s" % ch.id
		customTitle = self.getTableConfig(keyTitle) 
		if customTitle is not None:
			ch.title = customTitle
		cell.speak(speakTitle=speakTitle)
		cell.updatePosition()
		self.forceBrlWindow = False
		self.displayBraille()
		
	def speakRow(self, speakTitle=False):
		self.customizeColHeaders()
		key = "selectedCols_%s" % self.getTableIdentifier()
		try:
			self._selectedCols = self.userConfig[self.pageTitle][key]
		except:
			self._selectedCols = []
		cols = []
		for cs in self._selectedCols:
			cols.append(int(cs))
		if self._curCol not in cols:
			cols.append(self._curCol)
		cols.sort()
		for col in cols:
			cell = self.getCell(col)
			if cell is not None:
				cell.speak(speakTitle=False)
		self.forceBrlWindow = False
		cell = self.getCell()
		if cell is not None:
			cell.updatePosition()
		self.displayBraille()

	def displayBraille(self):
		s = ""
		selected = None
		window = 0
		self.brlPositions = []
		cells = self.getRow().getCells()
		if cells is None:
			return
		curColVisible = False
		for i in range(0, self.getColCount()):
			try:
				text = cells[i].brlText()
				selected = cells[i].selected
				visited = cells[i].visited
			except:
				text = "err"
				selected = False
				visited = False
			if len(s) + len(text) > braille.handler.displaySize:
				# we are more than the braikle window size
				if self.forceBrlWindow:
					if window == self.curBrlWindow:
						break
				else:
					if curColVisible:
						break
				# reset braille window computation
				s = ""
				self.brlPositions = []
				plage += 1
			start = len(s)
			end = start + len(text)
			self.brlPositions.append((start, end, i))
			s += text + " "
			if i == self._curCol-1:
				curColVisible = True
		if selected is None:
			return
		self.curBrlWindow = window

		# Deals with brailleHandler to print our newly generated braille window
		bh = braille.handler
		region = braille.TextRegion(s)
		region.obj = None
		region.update()
		if selected or visited:
			for x in xrange(len(region.brailleCells)):
				region.brailleCells[x] |= braille.DOT7 | braille.DOT8
		else:
			for pos in self.brlPositions:
				start, end, i = pos
				if i == self._curCol - 1:
					startWindow = False
					for x in xrange(len(region.brailleCells)):
						if x == start and startWindow is False:
							startWindow = True
						# if region.brailleCells[x] == 0x00 and x + 1 < end and region.brailleCells[x + 1] == 0x00:
							# startWindow = False
						if startWindow:
							region.brailleCells[x] |= braille.DOT7 | braille.DOT8
						if x == end - 1:
							startWindow = False
		bh.mainBuffer.clear()
		bh.mainBuffer.regions.append(region)
		bh.mainBuffer.update()
		bh.update()
		

	
	def brailleRouting(self, gesture):
		n = gesture.routingIndex
		if scriptHandler.getLastScriptRepeatCount() > 0:
			# double click
			self.enter()
			return
		for (start, end, col) in self.brlPositions:
			if n >= start and n < end:
				self._curCol = col+1
				self.speakCell()
				return
		lib.beep (440, 20)
		
	def brailleRight(self):
		self.forceBrlWindow = True
		self.curBrlWindow +=1
		self.displayBraille()
		
	def brailleLeft(self):
		if self.curBrlWindow <= 0:
			return
		self.forceBrlWindow = True
		self.curBrlWindow -= 1
		self.displayBraille()
		
	def rightCell (self):
		if self._curCol >= self._colCount:
			speech.speakMessage (u"fin")
		else:
			self._curCol += 1

	def leftCell(self):
		if self._curCol <= 1:
			speech.speakMessage (u"début")
		else:
			self._curCol -= 1
	

	def lastCell(self):
		self._curCol = self.getColCount()

	def firstCell(self):
		self._curCol = 1


	def setTableConfig(self, key, value):
		if self.pageTitle not in self.tableConfig:
			# if the section is not found, we create it
			self.tableConfig[self.pageTitle] = {}
		id = self.getTableIdentifier()
		if id != "":
			# it has an identifier, we create a subsection
			if id  not in self.tableConfig[self.pageTitle]:
				# create the subsection if not found
				self.tableConfig[self.pageTitle][id] = {}
			self.tableConfig[self.pageTitle][id][key] = value
		else:
			# no identifier, so we don't use a subsection
			self.tableConfig[self.pageTitle][key] = value
		self.tableConfig.write()
	
	def getTableConfig(self, key):
		try:
			return self.tableConfig[self.pageTitle][self.getTableIdentifier()][key]
		except:
			try:
				return self.tableConfig[self.pageTitle][key]
			except:
				return None
	
	def selectionCol(self):
		col = self._curCol
		speech.speakMessage (u"Colonne %s sélectionnée" % self._titlesCol[col-1].title)
		if col not in self._selectedCols:
			self._selectedCols.append (col) 
		if self.pageTitle not in self.userConfig:
			self.userConfig[self.pageTitle] = {}
		key = "selectedCols_%s" % self.getTableIdentifier()
		self.userConfig[self.pageTitle][key] = self._selectedCols
		self.userConfig.write()

	def resetSelectionCol(self):
		speech.speakMessage (u"sélection de colonnes effacée")
		self._selectedCols = []
		if self.pageTitle not in self.userConfig:
			self.userConfig[self.pageTitle] = {}
		key = "selectedCols_%s" % self.getTableIdentifier()
		self.userConfig[self.pageTitle][key] = self._selectedCols
		self.userConfig.write()
		
	def focusCurCell(self):
		self.getCell().setFocus()


	## table script.




	def script_enter(self, gesture):
		c = self.table.getCell()
		if c.role in (controlTypes.ROLE_EDITABLETEXT, controlTypes.ROLE_COMBOBOX):
			ui.message(u"Mode &dition non supporté")
			return
		ui.message(u"Ce tableau générique ne supporte pas cette touche.")

	def script_space(self, gesture):
		ui.message(u"Ce tableau générique ne supporte pas cette touche.")

	def script_controlSpace(self, gesture):
		ui.message(u"Ce tableau générique ne supporte pas cette touche.")

	def script_tab(self, gesture):
		self.table.rightCell()
		self.table.speakCell(speakTitle=True)

	def script_shiftTab(self, gesture):
		self.table.leftCell()
		self.table.speakCell(speakTitle=True)

	def script_downArrow(self, gesture):
		ui.message(u"Ce tableau générique ne supporte pas cette touche.")
		

	def script_upArrow(self, gesture):
		ui.message(u"Ce tableau générique ne supporte pas cette touche.")

	def script_rightArrow(self, gesture):
		if self.editColWidthMode is True:
			self.table.increaseColWidth()
			return
		self.tableau.rightCell()
		self.tableau.speakCell(speakTitle=True)

	def script_leftArrow(self, gesture):
		if self.editColWidthMode is True:
			self.table.decreaseColWidth()
			return
		self.table.leftCell()
		self.table.speakCell(speakTitle=True)

	def script_end(self, gesture):
		speech.speakMessage (u"dernière colonne")
		self.table.lastCell()
		self.table.speakCell(speakTitle=True)


	def script_home(self, gesture):
		speech.speakMessage (u"première colonne")
		self.table.firstCell()
		self.table.speakCell(speakTitle=True)

	def script_controlEnd(self, gesture):
		speech.speakMessage(u"dernière ligne")
		self.table.lastLine()
		self._tableau.speakRow ()

	def script_controlHome(self, gesture):
		speech.speakMessage (u"première ligne")
		self._tableau.firstLine ()
		self._tableau.speakRow ()


	def isBoutonPageSuivante (self, info):
		obj = info.NVDAObjectAtStart
		if obj is None:
			return False
		if controlTypes.STATE_UNAVAILABLE  in obj.states:
			return False
		s = lib.getElementDescription(obj, max=2)
		if s.find("pe_grid_pager_button_next") > 1:
			return True
		else:
			return False

	def isBoutonPagePrecedente (self, info):
		obj = info.NVDAObjectAtStart
		if obj is None:
			return False
		if controlTypes.STATE_UNAVAILABLE  in obj.states:
			return False
		s = lib.getElementDescription(obj, max=2)
		if s.find("pe_grid_pager_button_pred") > 1:
			return True
		else:
			return False



	def script_controlPageDown(self, gesture):
		if lib.searchTag ("button", func=self.isBoutonPageSuivante):
			speech.speakMessage (u"page suivante")
			obj = lib.getCaretObject ()
			obj.doAction()
		else:
			speech.speakMessage (u"pas de page suivante")

	def script_controlPageUp(self, gesture):
		if lib.searchTag ("button", func=self.isBoutonPagePrecedente):
			speech.speakMessage (u"page précédente")
			obj = lib.getCaretObject ()
			obj.doAction()
		else:
			speech.speakMessage (u"pas de page précédente")

	def script_controlDownarrow (self, gesture):
		speech.speakMessage (u"Sortie du tableau")
		focus = api.getFocusObject()
		focus = focus.treeInterceptor
		focus.script_movePastEndOfContainer (None)
		self.exitMode ()
		self.execute ("forceSortieTableau", params="ignore tableau")

	def script_controlUparrow (self, gesture):
		speech.speakMessage ("sortie du tableau")
		focus = api.getFocusObject()
		focus = focus.treeInterceptor
		lib.speechOff ()
		focus.script_moveToStartOfContainer (None)
		focus.script_moveByLine_back (None)
		focus.script_moveToStartOfContainer (None)
		lib.speechOn (0.1)
		focus.script_moveByLine_back (None)
		self.exitMode ()
		self.execute ("forceSortieTableau", params="")

	def script_copieCell (self, gesture):
		if scriptHandler.getLastScriptRepeatCount() == 0:
			value = self._tableau.getCell().name
			speech.speakMessage (u"copie de la cellule")
		else:
			value = ""
			for c in self._tableau.getRow().getCells():
				value += c.brlText() + " "
			speech.speakMessage (u"copie de la ligne ")
		speech.speakMessage (value)
		api.copyToClip (value)

	def script_selectionCol (self, gesture):
		if scriptHandler.getLastScriptRepeatCount()==0:
			self._tableau.selectionCol()
		else:
			self._tableau.resetSelectionCol ()
		
	def script_essai (self, gesture):
		speech.speakMessage ("essai dans mode tableau")

	def script_brailleRouting (self, gesture):
		self._tableau.brailleRouting (gesture)
		
	def script_brailleRight (self, gesture):
		self._tableau.brailleRight()

	def script_brailleLeft (self, gesture):
		self._tableau.brailleLeft()
	
	def script_editColumnHeader(self, gesture):
		def onEditColumnHeader(result):
			newTitle = newTitleDlg.GetValue()
			if newTitle is None or newTitle == ch.title:
				ui.message("Abandon modification")
				return
			ch.title = newTitle
			self._tableau.setTableConfig ("title_%s" % ch.id, ch.title)
			
		curCell= self._tableau.getCell()
		if curCell is None:
			ui.message (u"erreur")
			return
		ch = curCell.colHeader
		if ch is None:
			ui.message("Cette colonne n'a pas de titre")
			return
		newTitleDlg = wx.TextEntryDialog(gui.mainFrame, u"Entrez le nouveau titre pour cette colonne", u"Modifier titre de colonne", ch.title, wx.OK | wx.CANCEL)
		gui.runScriptModalDialog(newTitleDlg, onEditColumnHeader)

	def script_modeLargeurColonne (self, gesture):
		self._modeLargeurColonne = not self._modeLargeurColonne
		c = self._tableau.getCell()
		if self._modeLargeurColonne:
			speech.speakMessage (u"Modification largeur colonne %s" % c.colHeader.title)
		else:
			speech.speakMessage (u"Modification largeur colonne désactivée")


	def script_editCell (self, gesture):
		self.pushMode ("tableau_edition")
		self.execute ("tableau_edition.startEdition", tableau=self._tableau)
		
	def event_childExited (self, modeName):
		if modeName == "tableau_detail":
			self._tableau.speakRow(speakTitle=True)
		elif modeName == "tableau_edition":
			lib.sendGesture("tab")
			time.sleep (1)
			lib.curseurVirtuel()
			self._tableau.analyzeRow()
			self._tableau.speakRow()

	def script_nextCharacter (self, gesture):
		self._tableau.getCell ().nextCharacter ()
		
	def script_priorCharacter (self, gesture):
		self._tableau.getCell ().priorCharacter ()
		
	def script_ouvreZone (self, gesture):
		self.pushMode ("tableau_detail", tableau=self._tableau)
		


	__genericGestures = {
		"br(handytech):routing" : "brailleRouting",
		"br(handytech):left" : "brailleLeft",
		"br(handytech):right" : "brailleRight",
		"br(handytech):down" : "downArrow",
		"br(handytech):up" : "upArrow",
		"kb:enter": "enter",
		"kb:space": "space",
		"kb:control+space": "controlSpace",
		"kb:tab": "tab",
		"kb:shift+tab": "shiftTab",
		"kb:downarrow": "downArrow",
		"kb:uparrow": "upArrow",
		"kb:rightarrow": "rightArrow",
		"kb:leftarrow": "leftArrow",
		"kb:end": "end",
		"kb:home": "home",
		"kb:control+end": "controlEnd",
		"kb:control+home": "controlHome",
		"kb:control+pagedown": "controlPageDown",
		"kb:control+pageup": "controlPageUp",
		"kb:control+downarrow": "controlDownarrow",
		"kb:control+uparrow": "controlUparrow",
		"kb:control+c": "copieCell",
		"kb:control+f2": "editColumnHeader",
		"kb:f2" : "editCell",
		"kb:control+shift+c": "selectionCol",
		"br(handytech):b4+b2+b3" : "modeLargeurColonne",
		"kb:nvda+rightarrow" : "nextCharacter",
		"kb:nvda+leftarrow" : "priorCharacter",
		"kb:control+z" : "ouvreZone",
		"kb:control+shift+e": "essai",
	}
	def __init__(self, webApp, obj=None):
		super(GenericTable, self).__init__(webApp)


	def script_typeLetter(self, gesture):
		ui.message(u"Recherche non supportée")


class GenericTable(WebAppWidget):
