PY ?= python3
ARGS ?=

.PHONY: help demo mwe hold recommend subplots backend-probe sine high-fps geom-cache

help:  ## List available example targets
	@printf "%s\n" \
	"Targets:" \
	"  demo          - simple animated sin/cos (two windows; pacing + hold_windows)" \
	"  mwe           - GUI -> svg save -> GUI (matplotlib-native backend switching)" \
	"  hold          - hold_windows() demo (AnyKey/Enter behavior)" \
	"  recommend     - recommended_backend() demo (select before pyplot import)" \
	"  subplots      - visual subplots(num=..., clear=...) reuse test" \
	"  backend-probe - backend switching probe (use ARGS=...)" \
	"  sine          - animated sine demo (two windows; optional --fps pacing)" \
	"  high-fps      - high FPS two-window demo (line.set_ydata + plt.pause)" \
	"  geom-cache    - minimal geometry persistence demo (macosx)" \
	"" \
	"Examples:" \
	"  make backend-probe ARGS='--make-figure --switch svg --switch-back macosx --hold'"

demo:  ## two windows updated in a loop
	$(PY) examples/simple_animated_sine_demo.py

mwe:  ## GUI -> svg save -> GUI
	$(PY) examples/matplotlib_native_mwe.py

hold:  ## hold_windows() demo
	$(PY) examples/hold_windows_demo.py

recommend:  ## recommended_backend() demo
	$(PY) examples/recommended_backend_demo.py

subplots:  ## visual subplots() reuse test
	$(PY) examples/visual_subplots_test.py

backend-probe:  ## backend switching probe (ARGS=...)
	$(PY) examples/backend_switch_probe.py $(ARGS)

sine:  ## animated sine demo (two windows)
	$(PY) examples/animated_sine_demo.py $(ARGS)

high-fps:  ## high FPS two-window demo
	$(PY) examples/high_fps_two_windows.py $(ARGS)

geom-cache:  ## minimal geometry persistence demo (macosx)
	$(PY) examples/minimal_example_demo.py
