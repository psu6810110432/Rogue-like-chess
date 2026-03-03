# main.py
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from screens.main_menu import MainMenuScreen
from screens.match_setup.setup_screen import MatchSetupScreen
from screens.gameplay_screen import GameplayScreen
from screens.options_screen import OptionsScreen
from kivy.properties import StringProperty

class RogueChessApp(App):
    ai_difficulty = 'normal'  # ตั้งค่าความยากเริ่มต้นของ AI

    selected_unit_white = StringProperty('Medieval Knights') 
    selected_unit_black = StringProperty('Demon')
    
    def build(self):
        # สร้าง ScreenManager พร้อมเอฟเฟกต์เฟดตอนเปลี่ยนหน้า
        sm = ScreenManager(transition=FadeTransition())
        
        # เพิ่มหน้าจอต่างๆ เข้าไปในระบบ
        sm.add_widget(MainMenuScreen(name='main_menu')) # แนะนำให้เปลี่ยนเป็น main_menu ให้ตรงกับ setup_screen.py ที่เรียกหาตอนกด Back
        sm.add_widget(MatchSetupScreen(name='setup'))
        
        # 🚨 FIX: เปลี่ยนชื่อจาก 'game' เป็น 'gameplay' ให้ตรงกับที่ปุ่ม START BATTLE เรียกหา
        sm.add_widget(GameplayScreen(name='gameplay')) 
        
        sm.add_widget(OptionsScreen(name='options')) # เพิ่มหน้า Options เข้าระบบ
        
        return sm

if __name__ == "__main__":
    RogueChessApp().run()