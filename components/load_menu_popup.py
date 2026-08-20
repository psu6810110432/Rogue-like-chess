# components/load_menu_popup.py
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.app import App
from kivy.graphics import Color, Rectangle

try:
    from logic.save_manager import get_all_saves, delete_save, rename_save
except ImportError:
    pass

class LoadMenuPopup(Popup):
    def __init__(self, main_menu_ref, **kwargs):
        super().__init__(**kwargs)
        self.main_menu_ref = main_menu_ref
        self.title = "LOAD GAME (Select a World)"
        self.title_size = '20sp'
        self.size_hint = (0.7, 0.7)
        self.auto_dismiss = False
        self.separator_color = (0.2, 0.8, 0.2, 1)
        
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(self.main_layout)
        
        self.refresh_ui()

    def refresh_ui(self):
        self.main_layout.clear_widgets()
        
        try:
            saves = get_all_saves()
        except Exception as e:
            print("Error loading saves:", e)
            saves = []
        
        if not saves:
            self.main_layout.add_widget(Label(text="No Save Data Found.", font_size='22sp', color=(0.6, 0.6, 0.6, 1)))
        else:
            for save_data in saves:
                world_id, save_name, current_turn, last_played, is_autosave = save_data
                
                # กล่องหลักสำหรับแต่ละ Slot
                slot_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(90), padding=dp(10), spacing=dp(10))
                with slot_box.canvas.before:
                    Color(0.1, 0.1, 0.15, 1)
                    rect = Rectangle(pos=slot_box.pos, size=slot_box.size)
                slot_box.bind(pos=lambda inst, val, r=rect: setattr(r, 'pos', val), size=lambda inst, val, r=rect: setattr(r, 'size', val))
                
                # ตกแต่งข้อความให้เห็นชัดเจนว่าอันไหน Autosave
                color_hex = "ffaa00" if is_autosave else "ffffff"
                
                info_text = f"[b][color={color_hex}]{save_name}[/color][/b]\nTurn: {current_turn}   |   Last Played: {last_played}"
                info_lbl = Label(text=info_text, markup=True, halign='left', valign='middle', size_hint_x=0.55, font_size='16sp')
                info_lbl.bind(size=info_lbl.setter('text_size'))
                
                slot_box.add_widget(info_lbl)
                
                # ปุ่ม Load
                btn_load = Button(text="[b]LOAD[/b]", markup=True, size_hint_x=0.15, background_color=(0.2, 0.8, 0.2, 1))
                btn_load.bind(on_release=lambda btn, wid=world_id: self.load_game(wid))
                
                # ปุ่ม Edit
                btn_edit = Button(text="[b]EDIT[/b]", markup=True, size_hint_x=0.15, background_color=(0.8, 0.8, 0.2, 1))
                btn_edit.bind(on_release=lambda btn, wid=world_id, sname=save_name: self.edit_save(wid, sname))
                
                # ปุ่ม Delete
                btn_delete = Button(text="[b]DELETE[/b]", markup=True, size_hint_x=0.15, background_color=(0.8, 0.2, 0.2, 1))
                btn_delete.bind(on_release=lambda btn, wid=world_id: self.delete_save_slot(wid))
                
                slot_box.add_widget(btn_load)
                slot_box.add_widget(btn_edit)
                slot_box.add_widget(btn_delete)
                
                self.main_layout.add_widget(slot_box)

        # พื้นที่ว่างดันให้ปุ่ม Close อยู่ล่างสุด
        self.main_layout.add_widget(Label(size_hint_y=1))

        # ปุ่ม Close
        close_btn = Button(text="[b]CLOSE[/b]", markup=True, size_hint_y=None, height=dp(50), background_color=(0.5, 0.2, 0.2, 1))
        close_btn.bind(on_release=self.dismiss)
        self.main_layout.add_widget(close_btn)

    def load_game(self, world_id):
        App.get_running_app().play_click_sound()
        self.dismiss()
        self.main_menu_ref.load_world_and_play(world_id)

    def delete_save_slot(self, world_id):
        App.get_running_app().play_click_sound()
        delete_save(world_id)
        self.refresh_ui()

    def edit_save(self, world_id, current_name):
        App.get_running_app().play_click_sound()
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        txt_input = TextInput(text=current_name, multiline=False, font_size='18sp', size_hint_y=0.6)
        content.add_widget(txt_input)
        
        btn_box = BoxLayout(spacing=dp(10), size_hint_y=0.4)
        save_btn = Button(text="SAVE", background_color=(0.2, 0.8, 0.2, 1))
        cancel_btn = Button(text="CANCEL", background_color=(0.8, 0.2, 0.2, 1))
        
        btn_box.add_widget(save_btn)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)
        
        edit_pop = Popup(title="Rename World", content=content, size_hint=(0.5, 0.3), auto_dismiss=False)
        
        def on_save(instance):
            new_name = txt_input.text.strip()
            if new_name:
                rename_save(world_id, new_name)
                self.refresh_ui() # รีเฟรชหน้าต่าง LoadMenu ด้วย
            edit_pop.dismiss()
            
        save_btn.bind(on_release=on_save)
        cancel_btn.bind(on_release=edit_pop.dismiss)
        
        edit_pop.open()