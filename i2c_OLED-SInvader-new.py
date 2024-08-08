import time
from ctypes import *
import random

# Load the CH347 DLL
ch347_dll = windll.LoadLibrary("CH347DLLA64.dll")

# Game parameters
screen_width = 128
screen_height = 64
player_width = 5
player_height = 3
enemy_width = 5
enemy_height = 3
num_enemies = 10
enemy_rows = 2
bullet_speed = 6  # Increased bullet speed
player_speed = 6  # Further increased player speed
enemy_speed = 1   # Further decreased enemy speed
enemy_drop_speed = 2  # Further decreased enemy drop speed
player_fire_rate = 0.15  # Further increased player fire rate
enemy_fire_rate = 3.5  # Further decreased enemy fire rate

class OLED:
    def __init__(self, usb_dev=0, i2c_addr=0x3C):  # Default I2C address for OLED
        self.usb_id = usb_dev
        self.dev_addr = i2c_addr
        self.width = screen_width
        self.height = screen_height
        self.pages = self.height // 8

        # Create a buffer for the display
        self.buffer = [0x00] * (self.width * self.pages)

        # Open the USB device
        if ch347_dll.CH347OpenDevice(self.usb_id) != -1:
            print("USB CH347 Device Opened Successfully!")
            self.initialize_display()
        else:
            raise Exception("USB CH347 Open Failed!")

    def close_device(self):
        ch347_dll.CH347CloseDevice(self.usb_id)
        print("USB CH347 Device Closed.")

    def write_command(self, command):
        # Prepare the command buffer
        cmd = (c_byte * 3)()
        cmd[0] = self.dev_addr << 1  # I2C device address with write flag
        cmd[1] = 0x00  # Command mode
        cmd[2] = command  # Actual command

        # Perform the I2C write operation
        result = ch347_dll.CH347StreamI2C(self.usb_id, 3, cmd, 0, None)
        if result != 1:
            raise Exception(f"Failed to send command: {hex(command)}")

    def write_data(self, data):
        # Prepare data buffer
        data_packet = (c_byte * (len(data) + 2))()
        data_packet[0] = self.dev_addr << 1  # I2C device address with write flag
        data_packet[1] = 0x40  # Data mode

        for i in range(len(data)):
            data_packet[i + 2] = data[i]

        # Perform the I2C write operation
        result = ch347_dll.CH347StreamI2C(self.usb_id, len(data_packet), data_packet, 0, None)
        if result != 1:
            raise Exception("Failed to write data to OLED")

    def initialize_display(self):
        try:
            # Initialization sequence for a typical SSD1306 OLED
            init_sequence = [
                0xAE,  # Display OFF (sleep mode)
                0xD5,  # Set display clock divide ratio/oscillator frequency
                0x80,  # Set divide ratio
                0xA8,  # Set multiplex ratio(1 to 64)
                0x3F,  # 1/64 duty
                0xD3,  # Set display offset
                0x00,  # Not offset
                0x40,  # Set start line address
                0x8D,  # Charge pump setting
                0x14,  # Enable charge pump
                0x20,  # Memory addressing mode
                0x00,  # Horizontal addressing mode
                0xA1,  # Set segment re-map 0 to 127
                0xC8,  # Set COM output scan direction
                0xDA,  # Set COM pins hardware configuration
                0x12,  # COM pins
                0x81,  # Set contrast control
                0xCF,  # Contrast
                0xD9,  # Set pre-charge period
                0xF1,  # Pre-charge period
                0xDB,  # Set VCOMH deselect level
                0x40,  # VCOMH
                0xA4,  # Entire display ON
                0xA6,  # Set normal display
                0xAF   # Display ON
            ]
            for cmd in init_sequence:
                self.write_command(cmd)

            self.clear_display()

            print("OLED Initialized")
        except Exception as e:
            print(f"Initialization error: {e}")

    def clear_display(self):
        # Clear the buffer
        self.buffer = [0x00] * (self.width * self.pages)

    def draw_pixel(self, x, y, color=1):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return  # Out of bounds

        page = int(y // 8)  # Ensure this is an integer
        bit = int(y % 8)    # Ensure this is an integer
        index = int(x + page * self.width)  # Ensure index is an integer

        # Ensure index is within bounds
        if 0 <= index < len(self.buffer):
            if color:
                self.buffer[index] |= (1 << bit)
            else:
                self.buffer[index] &= ~(1 << bit)

    def draw_rect(self, x, y, width, height, color=1):
        for i in range(width):
            for j in range(height):
                self.draw_pixel(x + i, y + j, color)

    def draw_text(self, text, x, y):
        for i, char in enumerate(text):
            char_data = self.get_char_data(char)
            for j, byte in enumerate(char_data):
                for bit in range(8):
                    self.draw_pixel(x + i * 6 + j, y + bit, (byte >> bit) & 1)

    def get_char_data(self, char):
        # Simplified font data for alphanumeric characters (6x8)
        font = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x49, 0x49, 0x7A],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x41, 0x7F, 0x41],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x0C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x46, 0x49, 0x49, 0x49, 0x31],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x30, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x03, 0x04, 0x78, 0x04, 0x03],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x42, 0x61, 0x51, 0x49, 0x46],
            '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
            '7': [0x01, 0x71, 0x09, 0x05, 0x03],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
        }
        return font.get(char.upper(), [0x00] * 5)  # Default to space for unknown characters

    def update_display(self):
        # Write the buffer to the display
        for page in range(self.pages):
            self.write_command(0xB0 + page)  # Set page address
            self.write_command(0x00)         # Set lower column address
            self.write_command(0x10)         # Set higher column address
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

class SpaceInvadersGame:
    def __init__(self, oled):
        self.oled = oled
        self.reset_game()

    def reset_game(self):
        self.player_x = screen_width // 2 - player_width // 2
        self.player_y = screen_height - player_height - 1
        self.bullets = []  # Player bullets
        self.enemy_bullets = []  # Enemy bullets
        self.enemies = [
            (x * (enemy_width + 3), y * (enemy_height + 3))
            for y in range(enemy_rows)
            for x in range(num_enemies // enemy_rows)
        ]
        self.enemy_direction = 1
        self.player_last_fire_time = 0
        self.enemy_last_fire_time = 0
        self.game_over = False
        self.victory = False
        self.start_time = time.time()  # Track the start time of the game

    def move_player(self):
        # Move player towards the most threatening enemy
        if self.enemies:
            # Choose enemy based on distance and potential threat
            target_enemy = min(self.enemies, key=lambda e: (abs(e[0] - self.player_x), -e[1]))
            if self.player_x < target_enemy[0]:
                self.player_x += player_speed
            elif self.player_x > target_enemy[0]:
                self.player_x -= player_speed

        # Keep player within screen bounds
        self.player_x = max(0, min(self.player_x, screen_width - player_width))

    def fire_bullet(self):
        # Fire a bullet from the player's position if enough time has passed
        current_time = time.time()
        if len(self.bullets) < 3 and (current_time - self.player_last_fire_time > player_fire_rate):
            self.bullets.append((self.player_x + player_width // 2, self.player_y))
            self.player_last_fire_time = current_time

    def move_bullets(self):
        # Move player bullets
        self.bullets = [(x, y - bullet_speed) for x, y in self.bullets if y > 0]

    def move_enemies(self):
        # Move enemies horizontally
        edge_hit = False  # Track if any enemy hits an edge

        for i in range(len(self.enemies)):
            x, y = self.enemies[i]
            x += self.enemy_direction * enemy_speed
            self.enemies[i] = (x, y)

            # Check for edge hit
            if x <= 0 or x >= screen_width - enemy_width:
                edge_hit = True

        # If any enemy hits an edge, change direction and move all down
        if edge_hit:
            self.enemy_direction *= -1
            self.enemies = [(ex, ey + enemy_drop_speed) for ex, ey in self.enemies]

        # Randomly change direction to make the game less predictable
        if random.random() < 0.05:  # 5% chance of changing direction
            self.enemy_direction *= -1

    def enemy_fire_bullet(self):
        # Randomly fire a bullet from an enemy
        current_time = time.time()
        if current_time - self.enemy_last_fire_time > enemy_fire_rate:
            shooting_enemy = random.choice(self.enemies)
            self.enemy_bullets.append((shooting_enemy[0] + enemy_width // 2, shooting_enemy[1] + enemy_height))
            self.enemy_last_fire_time = current_time

    def move_enemy_bullets(self):
        # Move enemy bullets
        self.enemy_bullets = [(x, y + bullet_speed) for x, y in self.enemy_bullets if y < screen_height]

    def update_game_difficulty(self):
        # Increase difficulty based on elapsed time
        elapsed_time = time.time() - self.start_time

        global player_speed, enemy_speed, player_fire_rate, enemy_fire_rate

        if elapsed_time > 10:
            player_speed = min(7, player_speed + 0.1)  # Cap the speed increase
            enemy_speed = min(3, enemy_speed + 0.1)
            player_fire_rate = max(0.1, player_fire_rate - 0.01)  # Reduce the fire rate (increase speed)
            enemy_fire_rate = max(2.5, enemy_fire_rate - 0.05)

    def check_collisions(self):
        # Check for bullet collisions with enemies
        new_bullets = []
        for bx, by in self.bullets:
            hit = False
            for ex, ey in self.enemies:
                if (
                    ex <= bx <= ex + enemy_width and
                    ey <= by <= ey + enemy_height
                ):
                    self.enemies.remove((ex, ey))
                    hit = True
                    break
            if not hit:
                new_bullets.append((bx, by))
        self.bullets = new_bullets

        # Check for enemy bullets hitting the player
        for bx, by in self.enemy_bullets:
            if self.player_x <= bx <= self.player_x + player_width and self.player_y <= by <= self.player_y + player_height:
                self.game_over = True
                break

        # Check if any enemy reached the player's level
        for _, ey in self.enemies:
            if ey + enemy_height >= self.player_y:
                self.game_over = True
                break

    def draw(self):
        self.oled.clear_display()

        # Draw player
        self.oled.draw_rect(self.player_x, self.player_y, player_width, player_height)

        # Draw enemies
        for x, y in self.enemies:
            self.oled.draw_rect(x, y, enemy_width, enemy_height)

        # Draw bullets
        for x, y in self.bullets:
            self.oled.draw_pixel(x, y)

        # Draw enemy bullets
        for x, y in self.enemy_bullets:
            self.oled.draw_pixel(x, y)

        self.oled.update_display()

    def display_message(self, message):
        self.oled.clear_display()
        self.oled.draw_text(message, 0, screen_height // 2 - 4)
        self.oled.update_display()
        time.sleep(2)  # Display the message for 2 seconds

    def update(self):
        if self.game_over:
            print("Game Over: Invaders Win!")
            self.display_message("Invaders Win!")
            return True

        if not self.enemies:
            self.victory = True
            print("Victory: Player Wins!")
            self.display_message("Player Wins!")
            return True

        self.move_player()
        self.fire_bullet()
        self.move_bullets()
        self.move_enemies()
        self.enemy_fire_bullet()
        self.move_enemy_bullets()
        self.update_game_difficulty()
        self.check_collisions()
        self.draw()
        return False

def main():
    oled = OLED()
    game = SpaceInvadersGame(oled)

    player_wins = 0
    invader_wins = 0

    try:
        while True:
            if game.update():
                if game.victory:
                    player_wins += 1
                else:
                    invader_wins += 1
                
                # Calculate win percentage
                total_games = player_wins + invader_wins
                win_percentage = (player_wins / total_games) * 100 if total_games > 0 else 0

                # Print score and win percentage
                print(f"Score: Player Wins: {player_wins}, Invader Wins: {invader_wins}")
                print(f"Win Percentage: {win_percentage:.2f}%")
                
                time.sleep(2)  # Pause before restarting
                game.reset_game()
            time.sleep(0.02)  # Frame rate control
    finally:
        oled.close_device()

if __name__ == "__main__":
    main()
