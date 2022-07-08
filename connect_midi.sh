#!/bin/bash
gpio=$(jack_lsp -c | grep gpio | head -1)
jack_connect "$gpio" gx_head_amp:midi_in_1
echo "done"

