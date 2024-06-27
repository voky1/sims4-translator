# -*- coding: utf-8 -*-

import re
from PySide6.QtCore import Qt, QRect, QSize, QObject, Signal
from PySide6.QtWidgets import QWidget, QPlainTextEdit, QTextEdit, QMenu
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCursor, QPainter, QTextCharFormat, \
    QTextFormat, QTextOption, QIcon, QPen

import themes.light as light
import themes.dark as dark

from singletons.config import config
from singletons.interface import interface


class LineNumberArea(QWidget):

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class QTextEditor(QPlainTextEdit):

    selected = Signal(QObject)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.cursorPositionChanged.connect(self.highlightMatchingBracket)

        self.updateLineNumberAreaWidth(0)

        option = QTextOption()
        option.setFlags(QTextOption.ShowTabsAndSpaces | QTextOption.AddSpaceForLineAndParagraphSeparators)
        self.document().setDefaultTextOption(option)

        self.highlighter = BracketHighlighter(self.document())

        is_dark_theme = config.value('interface', 'theme') == 'dark'

        self.lines_color = QColor(dark.EDITOR_LINES) if is_dark_theme else QColor(light.EDITOR_LINES)
        self.lines_text = QColor(dark.EDITOR_LINES_TEXT) if is_dark_theme else QColor(light.EDITOR_LINES_TEXT)

        lines_border = dark.EDITOR_LINES_BORDER if is_dark_theme else light.EDITOR_LINES_BORDER
        self.lines_border = QColor(lines_border) if lines_border else None

        self.line_color = QColor(dark.EDITOR_LINE) if is_dark_theme else QColor(light.EDITOR_LINE)
        self.bracket_color = QColor(dark.EDITOR_BRACKET) if is_dark_theme else QColor(light.EDITOR_BRACKET)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        undo_action = menu.addAction(interface.text('TextEditor', 'Undo'))
        undo_action.setShortcut('Ctrl+Z')

        redo_action = menu.addAction(interface.text('TextEditor', 'Redo'))
        redo_action.setShortcut('Ctrl+Shift+Z')

        menu.addSeparator()

        cut_action = menu.addAction(interface.text('TextEditor', 'Cut'))
        cut_action.setShortcut('Ctrl+X')

        copy_action = menu.addAction(QIcon(':/images/copy.png'), interface.text('TextEditor', 'Copy'))
        copy_action.setShortcut('Ctrl+C')

        paste_action = menu.addAction(QIcon(':/images/paste.png'), interface.text('TextEditor', 'Paste'))
        paste_action.setShortcut('Ctrl+V')

        menu.addSeparator()

        select_all_action = menu.addAction(interface.text('TextEditor', 'Select All'))
        select_all_action.setShortcut('Ctrl+A')

        undo_action.triggered.connect(self.undo)
        redo_action.triggered.connect(self.redo)
        cut_action.triggered.connect(self.cut)
        copy_action.triggered.connect(self.copy)
        paste_action.triggered.connect(self.paste)
        select_all_action.triggered.connect(self.selectAll)

        menu.exec_(event.globalPos())

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 14 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(),
                                        self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), self.lines_color)

        if self.lines_border:
            painter.setPen(QPen(self.lines_border, 1))
            rect = event.rect()
            painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(self.lines_text)
                painter.drawText(0, top, self.lineNumberArea.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlightCurrentLine(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            selection.format.setBackground(self.line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)
    
    def highlightMatchingBracket(self):
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        pos = cursor.positionInBlock()
        char_before = text[pos-1] if pos > 0 else ''
        char_after = text[pos] if pos < len(text) else ''

        extra_selections = self.extraSelections()

        if not self.isReadOnly():
            for bracket in ('<>', '{}'):
                open_bracket = bracket[0]
                close_bracket = bracket[1]

                if char_before == open_bracket or char_after == open_bracket:
                    open_pos = pos - 1 if char_before == open_bracket else pos
                    close_pos = self.findMatchingBracket(block, open_pos, open_bracket, close_bracket)
                    if close_pos != -1:
                        extra_selections.append(self.createBracketSelection(cursor, open_pos))
                        extra_selections.append(self.createBracketSelection(cursor, close_pos))

                elif char_before == close_bracket or char_after == close_bracket:
                    close_pos = pos - 1 if char_before == close_bracket else pos
                    open_pos = self.findMatchingBracket(block, close_pos, close_bracket, open_bracket, reverse=True)
                    if open_pos != -1:
                        extra_selections.append(self.createBracketSelection(cursor, open_pos))
                        extra_selections.append(self.createBracketSelection(cursor, close_pos))

        self.setExtraSelections(extra_selections)

    def findMatchingBracket(self, block, pos, open_bracket, close_bracket, reverse=False):
        text = block.text()
        direction = -1 if reverse else 1
        stack = 0
        
        while 0 <= pos < len(text):
            char = text[pos]
            if char == open_bracket:
                stack += 1
            elif char == close_bracket:
                stack -= 1
                if stack == 0:
                    return pos
            pos += direction

        return -1

    def createBracketSelection(self, cursor, pos):
        selection = QTextEdit.ExtraSelection()
        
        fmt = QTextCharFormat()
        fmt.setBackground(self.bracket_color)
        selection.format = fmt

        new_cursor = self.textCursor()
        new_cursor.setPosition(cursor.block().position() + pos)
        new_cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        selection.cursor = new_cursor

        return selection

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.selected.emit(self)


class BracketHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        is_dark_theme = config.value('interface', 'theme') == 'dark'

        patterns_light = [
            (re.compile(r'{\w+\.[^}]+}'), None, True),
            (re.compile(r'{[Mm]\w+\.[^}]+}'), QColor(light.EDITOR_MALE), light.EDITOR_MALE_BOLD),
            (re.compile(r'{[Ff]\w+\.[^}]+}'), QColor(light.EDITOR_FEMALE), light.EDITOR_FEMALE_BOLD),
            (re.compile(r'{\d+\.(Sim)[^}]+}'), QColor(light.EDITOR_SIMNAME), light.EDITOR_SIMNAME_BOLD),
            (re.compile(r'<[^>]+>'), QColor(light.EDITOR_TAG), False),
            (re.compile(r'(\s)'), QColor(0, 0, 0, 0), False),
            (re.compile(r'(\s\s+)'), QColor(light.EDITOR_TAG), False)
        ]

        patterns_dark = [
            (re.compile(r'{\w+\.[^}]+}'), QColor('#fff'), True),
            (re.compile(r'{[Mm]\w+\.[^}]+}'), QColor(dark.EDITOR_MALE), dark.EDITOR_MALE_BOLD),
            (re.compile(r'{[Ff]\w+\.[^}]+}'), QColor(dark.EDITOR_FEMALE), dark.EDITOR_FEMALE_BOLD),
            (re.compile(r'{\d+\.(Sim)[^}]+}'), QColor(dark.EDITOR_SIMNAME), dark.EDITOR_SIMNAME_BOLD),
            (re.compile(r'<[^>]+>'), QColor(dark.EDITOR_TAG), False),
            (re.compile(r'(\s)'), QColor(0, 0, 0, 0), False),
            (re.compile(r'(\s\s+)'), QColor(dark.EDITOR_TAG), False)
        ]

        self.__patterns = patterns_dark if is_dark_theme else patterns_light

    def highlightBlock(self, text):
        for pattern, color, bold in self.__patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.getFormat(color, bold))

    def getFormat(self, color=None, bold=False):
        fmt = QTextCharFormat()
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if color:
            fmt.setForeground(color)
        return fmt
