import time

import asyncio

from adafruit_macropad import MacroPad

macropad = MacroPad()
text_lines = macropad.display_text(title="Tripl3Point StreamDeck")
aquarium_scene_key = 1
mute_key = 4
aquarium_blink_delay_sec = 3 * 60  # 3 minutes
mute_blink_delay_sec = 60  # 1 minute


async def monitor_keys():
    last_position = 0
    aquarium_blink_delay_timer_start = time.monotonic()
    mute_blink_delay_timer_start = time.monotonic()
    aquarium_scene_active = False
    muted = False

    aquarium_blink_task = None
    mute_blink_task = None

    print("Monitoring keys...")
    while True:
        # Get the current time using time.monotonic().
        time_now = time.monotonic()

        key_event = macropad.keys.events.get()

        if key_event:
            if key_event.pressed:
                text_lines[1].text = f"Key {key_event.key_number} pressed!"
                macropad.play_tone(292, 0.1)

                if key_event.key_number == 0:
                    macropad.keyboard.send(macropad.Keycode.F13)
                    text_lines[2].text = f"Gaming scene"
                    toggle_pixel_and_turn_off_other_pixels_except_mute(0)
                    aquarium_scene_active = False
                elif key_event.key_number == 1:
                    macropad.keyboard.send(macropad.Keycode.F14)
                    text_lines[2].text = f"Aquarium scene"
                    toggle_pixel_and_turn_off_other_pixels_except_mute(aquarium_scene_key)
                    aquarium_scene_active = True
                    aquarium_blink_delay_timer_start = time.monotonic()
                elif key_event.key_number == 2:
                    macropad.keyboard.send(macropad.Keycode.F15)
                elif key_event.key_number == 3:
                    macropad.keyboard.send(macropad.Keycode.F16)
                elif key_event.key_number == 4:
                    macropad.keyboard.send(macropad.Keycode.F17)
                    toggle_mute()
                    muted = update_mute_text()
                    mute_blink_delay_timer_start = time.monotonic()
                elif key_event.key_number == 5:
                    macropad.keyboard.send(macropad.Keycode.F18)
                elif key_event.key_number == 6:
                    macropad.keyboard.send(macropad.Keycode.F19)
                elif key_event.key_number == 7:
                    macropad.keyboard.send(macropad.Keycode.F20)
                elif key_event.key_number == 8:
                    macropad.keyboard.send(macropad.Keycode.F21)
                elif key_event.key_number == 9:
                    macropad.keyboard.send(macropad.Keycode.F22)

        macropad.encoder_switch_debounced.update()

        if macropad.encoder_switch_debounced.pressed:
            pass

        current_position = macropad.encoder

        if macropad.encoder > last_position:
            last_position = current_position

        if macropad.encoder < last_position:
            last_position = current_position

        text_lines.show()
        macropad.pixels.show()

        if aquarium_scene_active:
            if time_now - aquarium_blink_delay_timer_start > aquarium_blink_delay_sec:
                if aquarium_blink_task is None:
                    print('Aquarium blink timer expired. Creating blink task...')
                    aquarium_blink_task = asyncio.create_task(periodic(0.25, blink, aquarium_scene_key, 0.25))
        else:
            if aquarium_blink_task is not None:
                print('Canceling aquarium blink task...')
                # Stop the aquarium scene key from blinking if it's no longer selected
                aquarium_blink_task.cancel()
                aquarium_blink_task = None

        if muted:
            if time_now - mute_blink_delay_timer_start > mute_blink_delay_sec:
                if mute_blink_task is None:
                    print('Mute blink timer expired. Creating blink task...')
                    mute_blink_task = asyncio.create_task(periodic(0.25, blink, mute_key, 0.25))
        else:
            if mute_blink_task is not None:
                print('Canceling mute blink task...')
                # Stop the aquarium scene key from blinking if it's no longer selected
                mute_blink_task.cancel()
                mute_blink_task = None

        # Let another task run.
        await asyncio.sleep(0)


# helper function for running a target periodically
async def periodic(interval_sec, coro_name, *args, **kwargs):
    # loop forever
    while True:
        # wait an interval
        await asyncio.sleep(interval_sec)
        # await the target
        await coro_name(*args, **kwargs)


async def blink(pixel_number: int, interval: [float, int]) -> None:
    # It's a bit redundant when we call this with periodic which also has a sleep interval but it doesn't seem to hurt
    await asyncio.sleep(interval)
    key_state = macropad.pixels[pixel_number]
    macropad.pixels[pixel_number] = (255, 0, 0) if key_state == (0, 0, 0) else (0, 0, 0)


def toggle_mute():
    # Get current mute state
    mute_state = macropad.pixels[mute_key]

    # toggle pixel
    macropad.pixels[4] = (255, 0, 0) if mute_state == (0, 0, 0) else (0, 0, 0)


def update_mute_text() -> bool:
    # Get current mute state
    mute_state = macropad.pixels[mute_key]

    # Update text
    if mute_state == (0, 0, 0):
        text_lines[2].text = "Unmuted"
        return False
    else:
        text_lines[2].text = "Muted"
        return True


def toggle_pixel_and_turn_off_other_pixels_except_mute(key_number: int) -> None:
    # Save current mute button state
    mute_state = macropad.pixels[mute_key]

    # Turn off all other pixels
    macropad.pixels.fill(0)

    # Turn on given key pixel
    macropad.pixels[key_number] = (
        (0, 0, 255) if macropad.pixels[key_number] == (0, 0, 0) else (0, 0, 0)
    )

    # Set mute back to original state
    macropad.pixels[4] = mute_state


async def main():
    await asyncio.create_task(monitor_keys())


asyncio.run(main())
