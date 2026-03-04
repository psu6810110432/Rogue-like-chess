# logic/item_logic.py

class Item:
    def __init__(self, id, name, description, image_path):
        self.id = id
        self.name = name
        self.description = description
        self.image_path = image_path

ITEM_DATABASE = {
    1: Item(1, "Totem of Hollow Life", "Survive a lethal Crash, but Base Points drop to 0. (Consumable)", "assets/item/item1.png"),#fixed
    2: Item(2, "Clutch Protection", "Nullify the attacker's coin toss entirely for 1 turn. (Consumable)", "assets/item/item2.png"), #fixed
    3: Item(3, "Bloodlust Emblem", "Gain +5 Base Points upon winning a Crash. (Consumable)", "assets/item/item3.png"),#balance pass 
    4: Item(4, "Mirage Shield", "Block and cancel an incoming attack completely. (Consumable)", "assets/item/item4.png"), #fixed
    5: Item(5, "Scythe of the Substitute", "Spawns a friendly Pawn on this tile upon death.", "assets/item/item5.png"), #fixed
    6: Item(6, "Gambler's Coin", "+1 Coin but permanently lose 2 Base Point.", "assets/item/item6.png"),#balance pass
    7: Item(7, "Armor of Thorns", "If killed, the attacker permanently loses 1 Coin.", "assets/item/item7.png"),#pass
    8: Item(8, "Aura of Misfortune", "Reduces the attacker's coins by 1 during a Crash.", "assets/item/item8.png"),#pass
    9: Item(9, "Pegasus Boots", "Can leap over other pieces like a Knight.(expect Knight)", "assets/item/item9.png"),#pass
    10: Item(10, "Crown of the Usurper", "Pawn only: Base Points become 5 and Coins become 3.", "assets/item/item10.png"),#unbalance #pass
}