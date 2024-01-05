#!/bin/bash

toggle_tap_to_click() {
    local touchpad_id="$1"

    if [ -z "$touchpad_id" ]; then
        echo "No touchpad ID provided."
        exit 1
    fi

    local tap_to_click_code=$(xinput --list-props "$touchpad_id" | awk '/Tapping Enabled \(/ {print $4}' | grep -o '[0-9]\+')

    if [[ $(xinput --list-props "$touchpad_id" | awk '/Tapping Enabled \(/ {print $5}') == 1 ]]; then
        xinput --set-prop "$touchpad_id" "$tap_to_click_code" 0
        echo "Tap to click is now disabled"
    else
        xinput --set-prop "$touchpad_id" "$tap_to_click_code" 1
        echo "Tap to click is now enabled"
    fi
}

# Call the function with the provided touchpad ID
toggle_tap_to_click "$@"

