from src.client.client import Client
from src.client.screens import *
from src.shared.physics.objects import Inventory


class Slot(Button):
    def __init__(self, x, y, offset, width, height, inventory: Inventory, slot_index: int, texture=None):
        super().__init__(x, y, offset, width, height, texture)
        self.inventory = inventory
        self.slot_index = slot_index

    def get_item(self):
        return self.inventory.items[self.slot_index]

    def set_item(self, item_stack):
        self.inventory.items[self.slot_index] = item_stack



class InventoryScreen(Screen):
    def __init__(self, title: str, main_inventory: Inventory, secondary_inventory: Inventory | None = None):
        self.actions = []
        self.title = title
        self.main_inventory = main_inventory
        self.secondary_inventory = secondary_inventory

        # UI components
        bg = Image(0.5, 0.5, (0, 0), 1.0, 1.0, "inventory_bg.png")
        self.labels = [TextLabel(0.5, 0.05, (0, 0), "default_font", title)]

        # Generate slots
        self.slots = []
        self._create_inventory_slots()

        # Collect UI parts for Screen
        super().__init__(bg, self.labels + self.slots, self.slots)

    def _create_inventory_slots(self):
        slot_size = 0.08  # % of screen
        spacing = 0.01
        cols = 9  # classic grid layout

        def make_grid(inv, y_start, rows=3):
            slots = []
            for row in range(rows):
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= inv.size:
                        break
                    slot = Slot(
                        x=0.5 + (col - cols / 2) * (slot_size + spacing),
                        y=y_start + row * (slot_size + spacing),
                        offset=(0, 0),
                        width=slot_size,
                        height=slot_size,
                        inventory=inv,
                        slot_index=idx,
                        texture="slot.png"
                    )
                    slots.append(slot)
            return slots

        # Player inventory at bottom
        self.slots.extend(make_grid(self.main_inventory, y_start=0.6, rows=3))

        # Secondary inventory (chest, furnace, etc.) at top
        if self.secondary_inventory:
            self.slots.extend(make_grid(self.secondary_inventory, y_start=0.2, rows=max(1, self.secondary_inventory.size // 9)))

    def handle_click(self, client):
        for slot in self.slots:
            if slot.is_pressed(True, Vec2(client.screenWidth, client.screenHeight), client.mouse_pos, client.camera.get_scale()):
                self.handle_slot_click(slot, client)

    def handle_slot_click(self, slot: Slot, client: Client):
        """Handles moving items with mouse_inventory"""
        item = slot.get_item()

        # Case 1: Mouse is empty, pick item
        if client.mouse_inventory is None and item:
            client.mouse_inventory = item
            slot.set_item(None)

        # Case 2: Mouse has item, try placing
        elif client.mouse_inventory:
            if item is None:
                slot.set_item(client.mouse_inventory)
                client.mouse_inventory = None
            elif item.item.tile_type == client.mouse_inventory.item.tile_type:
                item.count += client.mouse_inventory.count
                client.mouse_inventory = None
            else:
                # Swap items
                tmp = slot.get_item()
                slot.set_item(client.mouse_inventory)
                client.mouse_inventory = tmp
