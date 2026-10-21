include(boards/mpconfigboard_esp32_common.cmake)

list(APPEND SDKCONFIG_DEFAULTS
    boards/sdkconfig.csi
    boards/sdkconfig.ble_single_connection
)

set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/../ESPIDE/manifest.py)
