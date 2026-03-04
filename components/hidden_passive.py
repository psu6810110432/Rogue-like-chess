# Hidden Passive System
# ระบบ passive แฝงสำหรับหมากแต่ละตัว

import random

class HiddenPassive:
    """จัดการ passive แฝงของหมากแต่ละตัว"""
    
    # กำหนดโอกาสการได้รับ passive (รวม 100%)
    PASSIVE_CHANCES = {
        'no_passive': 74,      # 74% ไม่ได้ passive ใดๆ
        'buff1': 3,            # 3% ได้ buff1 (เหรียญ +1)
        'buff2': 15,           # 15% ได้ buff2 (แต้ม +2/+3)
        'debuff1': 3,          # 3% ได้ debuff1 (เหรียญ -1)
        'debuff2': 5          # 5% ได้ debuff2 (แต้ม -1/-2)
    }
    
    # กำหนดคำอธิบาย passive แต่ละประเภท
    PASSIVE_VALUES = {
        'buff1': {
            'description': 'เหรียญทอยเพิ่ม'
        },
        'buff2': {
            'description': 'แต้มเริ่มต้นเพิ่ม'
        },
        'debuff1': {
            'description': 'เหรียญทอยลด'
        },
        'debuff2': {
            'description': 'แต้มเริ่มต้นลด'
        }
    }
    
    def __init__(self):
        self.passive_type = None
        self.passive_value = None
        self.description = None
        self._generate_passive()
    
    def _generate_passive(self):
        """สุ่มสร้าง passive แฝง"""
        # สุ่มตามโอกาสที่กำหนด
        rand_num = random.randint(1, 100)
        cumulative = 0
        
        for passive_type, chance in self.PASSIVE_CHANCES.items():
            cumulative += chance
            if rand_num <= cumulative:
                self.passive_type = passive_type
                break
        
        # ถ้าไม่ได้ passive ใดๆ
        if self.passive_type == 'no_passive' or self.passive_type is None:
            self.passive_type = None
            self.passive_value = {}
            self.description = 'ไม่มี passive แฝง'
            return
        
        # กำหนดค่า passive ให้ตรงตามคอมเมนต์
        if self.passive_type in ['buff1', 'debuff1']:
            if self.passive_type == 'buff1':
                coin_modifier = 1  # buff: เหรียญเพิ่ม 1 เสมอ
            else:  # debuff1
                coin_modifier = -1  # debuff: เหรียญลด 1 เสมอ
            self.passive_value = {'coins': coin_modifier}
            
        elif self.passive_type in ['buff2', 'debuff2']:
            if self.passive_type == 'buff2':
                point_modifier = random.choice([2, 3])  # buff: แต้มเพิ่ม 2 หรือ 3
            else:  # debuff2
                point_modifier = random.choice([-1, -2])  # debuff: แต้มลด 1 หรือ 2
            self.passive_value = {'points': point_modifier}
        
        self.description = self.PASSIVE_VALUES[self.passive_type]['description']
    
    def apply_passive(self, base_points, base_coins):
        """ปรับค่าพลังตาม passive ที่ได้รับ"""
        if not self.passive_type:
            return base_points, base_coins
        
        new_points = base_points
        new_coins = base_coins
        
        if 'points' in self.passive_value:
            new_points += self.passive_value['points']
            # ไม่ให้แต้มต่ำกว่า 0
            new_points = max(0, new_points)
        
        if 'coins' in self.passive_value:
            new_coins += self.passive_value['coins']
            # ไม่ให้เหรียญต่ำกว่า 0
            new_coins = max(0, new_coins)
        
        return new_points, new_coins
    
    def get_passive_info(self):
        """ดึงข้อมูล passive สำหรับแสดงผล"""
        if not self.passive_type:
            return {
                'type': None,
                'description': 'ไม่มี passive แฝง',
                'modifier': {}
            }
        
        modifier_text = ''
        if 'coins' in self.passive_value:
            modifier_text = f"{self.passive_value['coins']} เหรียญ"
        elif 'points' in self.passive_value:
            modifier_text = f"{self.passive_value['points']} แต้ม"
        
        return {
            'type': self.passive_type,
            'description': self.description,
            'modifier': modifier_text,
            'values': self.passive_value
        }