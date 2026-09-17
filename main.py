"""
My Tasks - A Kivy to-do list app for Android.
Single-file, persistent, touch-optimized.
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty, BooleanProperty, NumericProperty
)
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# Keep the keyboard from covering the TextInput on Android
Window.softinput_mode = 'below_target'

# Desktop preview size (ignored on Android/iOS)
if platform not in ('android', 'ios'):
    Window.size = (400, 720)


def escape_markup(s):
    """Escape Kivy markup characters so user input renders literally."""
    return (s.replace('&', '&amp;')
             .replace('[', '&bl;')
             .replace(']', '&br;'))


# ---------------------------------------------------------------------------
# KV UI definition
# ---------------------------------------------------------------------------
KV = r"""
<TaskRow>:
    size_hint_y: None
    height: dp(58)
    padding: dp(6), dp(4)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: (1, 1, 1, 0.055)
        Rectangle:
            pos: self.pos
            size: self.size

    CheckBox:
        size_hint_x: None
        width: dp(46)
        active: root.done
        on_active: root.on_check_toggle(self.active)
        color: (0.25, 0.72, 1, 1)

    Label:
        text: root.display_text
        markup: True
        font_size: '16sp'
        color: (0.52, 0.56, 0.61, 1) if root.done else (0.95, 0.96, 0.97, 1)
        valign: 'middle'
        halign: 'left'
        shorten: True
        shorten_from: 'right'
        text_size: self.width, self.height

    Button:
        text: 'X'
        size_hint_x: None
        width: dp(46)
        font_size: '16sp'
        bold: True
        background_normal: ''
        background_down: ''
        background_color: (0.85, 0.28, 0.32, 0.85)
        color: (1, 1, 1, 1)
        on_press: root.on_delete_press()


<RootWidget>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 0.09, 0.10, 0.13, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # ---------- Header ----------
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: dp(62)
        padding: dp(16), dp(10)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 0.14, 0.16, 0.20, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'My Tasks'
            bold: True
            font_size: '22sp'
            color: (1, 1, 1, 1)
            halign: 'left'
            valign: 'middle'
            text_size: self.size

        Label:
            text: root.counter_text
            font_size: '14sp'
            color: (0.55, 0.60, 0.66, 1)
            size_hint_x: None
            width: dp(86)
            halign: 'right'
            valign: 'middle'
            text_size: self.size

        Button:
            text: 'Clear done'
            font_size: '12sp'
            size_hint_x: None
            width: dp(84)
            background_normal: ''
            background_down: ''
            background_color: (0.30, 0.32, 0.38, 1)
            color: (1, 1, 1, 1)
            opacity: 1 if root.done_count > 0 else 0
            disabled: root.done_count == 0
            on_press: root.clear_done()

    # ---------- Input row ----------
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: dp(68)
        padding: dp(12), dp(10)
        spacing: dp(8)

        TextInput:
            id: task_input
            hint_text: 'What needs to be done?'
            multiline: False
            font_size: '16sp'
            background_normal: ''
            background_active: ''
            background_color: (0.18, 0.20, 0.25, 1)
            foreground_color: (0.95, 0.96, 0.97, 1)
            hint_text_color: (0.45, 0.50, 0.56, 1)
            cursor_color: (0.25, 0.72, 1, 1)
            padding: dp(12), dp(14)
            on_text_validate: root.add_task()

        Button:
            text: 'Add'
            size_hint_x: None
            width: dp(72)
            font_size: '16sp'
            bold: True
            background_normal: ''
            background_down: ''
            background_color: (0.25, 0.72, 1, 1)
            color: (1, 1, 1, 1)
            on_press: root.add_task()

    # ---------- Task list ----------
    ScrollView:
        id: scroll
        do_scroll_x: False
        bar_width: dp(3)
        bar_color: (0.3, 0.7, 1, 0.5)
        bar_inactive_color: (0.3, 0.7, 1, 0.2)

        BoxLayout:
            id: task_list
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            padding: 0, dp(4), 0, dp(24)
            spacing: dp(2)

            Label:
                text: 'Nothing here yet!\nAdd your first task above.'
                font_size: '15sp'
                color: (0.42, 0.47, 0.53, 1)
                halign: 'center'
                valign: 'middle'
                text_size: self.size
                size_hint_y: None
                height: dp(120) if root.task_count == 0 else 0
                opacity: 1 if root.task_count == 0 else 0
"""


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
class TaskRow(BoxLayout):
    """A single row in the task list."""

    text = StringProperty('')
    done = BooleanProperty(False)
    task_id = NumericProperty(0)
    display_text = StringProperty('')

    # Plain class attributes (not Kivy properties) — set after construction
    toggle_cb = None
    delete_cb = None

    # Class-level default: blocks the checkbox callback during KV rule
    # application, which happens inside super().__init__().
    _syncing = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_display()
        self._syncing = False

    def on_text(self, *args):
        self._refresh_display()

    def on_done(self, *args):
        self._refresh_display()

    def _refresh_display(self):
        esc = escape_markup(self.text)
        self.display_text = '[s]{}[/s]'.format(esc) if self.done else esc

    def on_check_toggle(self, active):
        if self._syncing:
            return
        if active == self.done:
            return
        self.done = active
        if self.toggle_cb:
            self.toggle_cb(self.task_id, active)

    def on_delete_press(self):
        if self.delete_cb:
            self.delete_cb(self.task_id)


class RootWidget(BoxLayout):
    """Main app container: header, input, and scrollable task list."""

    counter_text = StringProperty('')
    task_count = NumericProperty(0)
    done_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore('tasks.json')
        self.tasks = []
        self._next_id = 1
        Clock.schedule_once(self._load, 0)

    # ---------------- persistence ----------------
    def _load(self, dt=0):
        try:
            if self.store.exists('data'):
                d = self.store.get('data')
                self.tasks = list(d.get('tasks', []))
                self._next_id = int(d.get('next_id', 1))
        except Exception:
            self.tasks = []
            self._next_id = 1
        self._rebuild()

    def _save(self):
        try:
            self.store.put('data', tasks=self.tasks, next_id=self._next_id)
        except Exception:
            pass  # never crash the UI over a storage hiccup

    # ---------------- actions ----------------
    def add_task(self):
        ti = self.ids.task_input
        txt = ti.text.strip()
        if not txt:
            return
        self.tasks.append({
            'id': self._next_id,
            'text': txt,
            'done': False,
        })
        self._next_id += 1
        ti.text = ''
        self._save()
        self._rebuild()
        Clock.schedule_once(self._scroll_to_bottom, 0.05)

    def _scroll_to_bottom(self, dt=0):
        try:
            self.ids.scroll.scroll_y = 0
        except Exception:
            pass

    def _toggle(self, task_id, done):
        for t in self.tasks:
            if t.get('id') == task_id:
                t['done'] = bool(done)
                break
        self._save()
        self._update_counter()

    def _delete(self, task_id):
        self.tasks = [t for t in self.tasks if t.get('id') != task_id]
        self._save()
        self._rebuild()

    def clear_done(self):
        self.tasks = [t for t in self.tasks if not t.get('done')]
        self._save()
        self._rebuild()

    # ---------------- rendering ----------------
    def _rebuild(self):
        container = self.ids.task_list

        # Remove only TaskRow widgets; keep the empty-state Label intact
        for child in list(container.children):
            if isinstance(child, TaskRow):
                container.remove_widget(child)

        for t in self.tasks:
            row = TaskRow(
                task_id=t.get('id', 0),
                text=t.get('text', ''),
                done=bool(t.get('done', False)),
            )
            row.toggle_cb = self._toggle
            row.delete_cb = self._delete
            container.add_widget(row)

        self._update_counter()

    def _update_counter(self):
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.get('done'))
        self.task_count = total
        self.done_count = done
        if total == 0:
            self.counter_text = ''
        elif done == total:
            self.counter_text = 'All done!'
        else:
            self.counter_text = '{} left'.format(total - done)


class TodoApp(App):
    def build(self):
        self.title = 'My Tasks'
        Builder.load_string(KV)
        return RootWidget()


if __name__ == '__main__':
    TodoApp().run()
