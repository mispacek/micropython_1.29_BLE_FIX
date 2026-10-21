include(boards/mpconfigboard_esp32c3_common.cmake)

list(APPEND SDKCONFIG_DEFAULTS
    boards/sdkconfig.csi
    boards/sdkconfig.ble_wifi_coex
)

set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/../ESPIDE/manifest.py)
